from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, create_engine
from passlib.context import CryptContext
from typing import List, Optional
from pydantic import BaseModel, constr, conint
import enum
import uuid
import secrets

app = FastAPI()

DATABASE_URL = "sqlite:///./orders.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# --- MODELS ---

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    orders = relationship("Order", back_populates="user")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="orders")

# --- Pydantic Schemas ---

class OrderCreate(BaseModel):
    item_name: constr(min_length=2, max_length=50)
    quantity: conint(gt=0, le=100)

class OrderOut(BaseModel):
    id: int
    item_name: str
    quantity: int
    status: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

# --- SIMPLE FAKE USER STORE ---

fake_users_db = {
    "alice": {
        "username": "alice",
        "hashed_password": pwd_context.hash("wonderland"),
        "id": 1
    },
    "bob": {
        "username": "bob",
        "hashed_password": pwd_context.hash("builder"),
        "id": 2
    }
}

# --- UTILS ---

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_user(db, username: str):
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if user and verify_password(password, user.hashed_password):
        return user
    return None

def create_access_token(username: str):
    # For demo: fake JWT
    return secrets.token_hex(24) + username

def get_current_user(token: str = Depends(oauth2_scheme), db: SessionLocal = Depends(lambda: SessionLocal())):
    # For demo: token ends with username
    username = token[-5:]
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return user

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Seed fake users if table is empty
    if db.query(User).count() == 0:
        for username, data in fake_users_db.items():
            user = User(username=username, hashed_password=data["hashed_password"])
            db.add(user)
        db.commit()
    db.close()

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = db.query(User).filter(User.username == form_data.username).first()
    db.close()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(user.username)
    return {"access_token": token, "token_type": "bearer"}

# --- ORDER PROCESSING BACKGROUND TASK ---

def process_order(order_id: int):
    import time
    db = SessionLocal()
    order = db.query(Order).get(order_id)
    if not order:
        db.close()
        return
    order.status = OrderStatus.PROCESSING
    db.commit()
    time.sleep(2)
    order.status = OrderStatus.COMPLETED
    db.commit()
    db.close()

@app.post("/orders/", response_model=OrderOut, status_code=201)
def submit_order(order_in: OrderCreate, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    order = Order(
        item_name=order_in.item_name,
        quantity=order_in.quantity,
        status=OrderStatus.PENDING,
        user_id=current_user.id
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    background_tasks.add_task(process_order, order.id)
    db.close()
    return order

@app.get("/orders/", response_model=List[OrderOut])
def list_orders(current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    orders = db.query(Order).filter(Order.user_id == current_user.id).all()
    db.close()
    return orders

@app.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    db.close()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
