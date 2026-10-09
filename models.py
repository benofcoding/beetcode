from typing import Any, Dict, List

from flask_login import UserMixin
from sqlalchemy import ForeignKey, JSON, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base, UserMixin):
    __tablename__ = "User"
    user_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    hash: Mapped[str] = mapped_column(String)

    user_problems: Mapped[list["User_Problem"]] = \
        relationship("User_Problem", back_populates="user")

    @property
    def id(self):
        return self.user_id


class User_Problem(Base):
    __tablename__ = "User_Problem"
    user_problem_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("User.user_id"))
    problem_id: Mapped[int] = mapped_column(ForeignKey("Problem.problem_id"))
    solution: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)

    problem: Mapped["Problem"] = \
        relationship("Problem", back_populates="user_problems")
    user: Mapped["User"] = relationship("User", back_populates="user_problems")


class Problem(Base):
    __tablename__ = "Problem"
    problem_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String)
    function_name: Mapped[str] = mapped_column(String)
    function_args: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    problem_name: Mapped[str] = mapped_column(String)
    difficulty: Mapped[str] = mapped_column(String)

    user_problems: Mapped[list["User_Problem"]] = \
        relationship("User_Problem", back_populates="problem")

    tests: Mapped[List["Test"]] = \
        relationship("Test", back_populates="problem")

    problem_tags: Mapped[List["Problem_Tag"]] = \
        relationship("Problem_Tag", back_populates="problem")


class Test(Base):
    __tablename__ = "Test"
    test_id: Mapped[int] = mapped_column(primary_key=True)
    test: Mapped[Dict[str, Any]] = mapped_column(JSON)
    type: Mapped[str] = mapped_column(String)
    problem_id: Mapped[int] = mapped_column(ForeignKey("Problem.problem_id"))
    test_num: Mapped[int]
    result: Mapped[str] = mapped_column(String)

    problem: Mapped["Problem"] = \
        relationship("Problem", back_populates="tests")


class Problem_Tag(Base):
    __tablename__ = "Problem_Tag"
    problem_tag_id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("Problem.problem_id"))
    tag_id: Mapped[int] = mapped_column(ForeignKey("Tag.tag_id"))

    problem: Mapped["Problem"] = \
        relationship("Problem", back_populates="problem_tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="problem_tags")


class Tag(Base):
    __tablename__ = "Tag"
    tag_id: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[str] = mapped_column(String)

    problem_tags: Mapped[List["Problem_Tag"]] = \
        relationship("Problem_Tag", back_populates="tag")


engine = create_engine("sqlite:///instance/database.db")
