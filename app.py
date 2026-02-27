from flask import Flask, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, select

app = Flask(__name__)
app.config["SECRET_KEY"] = "a-very-secret-secret-key"


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "User"
    user_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    hash: Mapped[str] = mapped_column(String)

class Problem(Base):
    __tablename__ = "Problem"
    problem_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String)

class Tag(Base):
    __tablename__ = "Tag"
    tag_id: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[str] = mapped_column(String)

class Testcase(Base):
    __tablename__ = "Testcase"
    testcase_id: Mapped[int] = mapped_column(primary_key=True)
    testcase: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    problem_id: Mapped[Problem] = relationship(back_populates="problem_id")









@app.route("/")
def home():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)