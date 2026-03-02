from flask import Flask, render_template, redirect, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import (DeclarativeBase,
                            Mapped,
                            mapped_column,
                            relationship,
                            Session)
from sqlalchemy import String, ForeignKey, select, create_engine
from typing import List, Any
import subprocess
import sys
import json

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

    user_problems: Mapped[list["User_Problem"]] = relationship("User_Problem", back_populates="user")


class User_Problem(Base):
    __tablename__ = "User_Problem"
    user_problem_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("User.user_id"))
    problem_id: Mapped[int] = mapped_column(ForeignKey("Problem.problem_id"))
    solution: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)

    problem: Mapped["Problem"] = relationship("Problem", back_populates="user_problems")
    user: Mapped["User"] = relationship("User", back_populates="user_problems")


class Problem(Base):
    __tablename__ = "Problem"
    problem_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String)
    function_name: Mapped[str] = mapped_column(String)

    user_problems: Mapped[list["User_Problem"]] = relationship("User_Problem", back_populates="problem")

    tests: Mapped[List["Test"]] = relationship("Test", back_populates="problem")

    problem_tags: Mapped[List["Problem_Tag"]] = relationship("Problem_Tag", back_populates="problem")


class Problem_Tag(Base):
    __tablename__ = "Problem_Tag"
    problem_tag_id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("Problem.problem_id"))
    tag_id: Mapped[int] = mapped_column(ForeignKey("Tag.tag_id"))

    problem: Mapped["Problem"] = relationship("Problem", back_populates="problem_tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="problem_tags")


class Tag(Base):
    __tablename__ = "Tag"
    tag_id: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[str] = mapped_column(String)

    problem_tags: Mapped[List["Problem_Tag"]] = relationship("Problem_Tag", back_populates="tag")


class Test(Base):
    __tablename__ = "Test"
    test_id: Mapped[int] = mapped_column(primary_key=True)
    test: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    problem_id: Mapped[int] = mapped_column(ForeignKey("Problem.problem_id"))

    problem: Mapped["Problem"] = relationship("Problem", back_populates="tests")


engine = create_engine("sqlite:///instance/database.db")  # or your DB URL











@app.route("/")
def home():
    return render_template('index.html')


@app.route("/problem/<int:problem_id>")
def problem(problem_id):
    return render_template('problem.html')


@app.route('/run_code', methods=['POST'])
def your_route():
    data = request.get_json()
    code = data['code']
    code = code.replace('\n', '\n    ')

    func_name = 'hi_benji' #GET REAL FUNC NAME FROM DATABASE DO LATER
    input_variables = {'name':'benjiriono'} #GET REAL INPUT VARIABLES FROM DATABASE DO LATER


    wrapper = f"""
    import json, sys
    data = json.loads(sys.stdin.read())

    {code}

    result = {func_name}(**data)
    
    if result is not None:
        print('__RETURN__',  result)
    """

    wrapper = wrapper.replace('\n    ', '\n')

    result = subprocess.run(
        [sys.executable, "-c", wrapper],
        input=json.dumps(input_variables),
        capture_output=True, text=True, timeout=5
    )

    

    return jsonify({ 'output':result.stdout, 'error':result.stderr})



if __name__ == "__main__":
    app.run(debug=True)