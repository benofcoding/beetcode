import json
import subprocess
import sys

from flask import jsonify, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import select
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import PasswordField, SelectField, StringField, SubmitField, validators
from wtforms.validators import DataRequired

from app import app, login_manager
from models import Problem, Test, User, User_Problem, engine


class LoginForm(FlaskForm):
    username = StringField(
        "Name",
        validators=[validators.InputRequired(message="Username is required")]
    )
    password = PasswordField(
        'Password',
        validators=[validators.InputRequired(message="Password is required")]
    )


class SignupForm(FlaskForm):
    username = StringField(
        "Name",
        validators=[validators.InputRequired(message="Username is required"),
                    validators.Length(min=3, max=20,
                                      message="Username must be "
                                      "between 3 and 20 characters")])
    password = PasswordField('Password',
                             validators=[
                             validators.InputRequired(message="Password "
                                                       "is required")])
    password_confirm = PasswordField('Password confirm', validators=[
            validators.InputRequired(message="Password confirmation "
                                     "is required"),
            validators.EqualTo('password', message='Passwords must match')])


class ProblemListForm(FlaskForm):
    """form for the filters on the problem list page"""
    sort_by = SelectField('Sort by', choices=[('problem_id', 'ID'),
                                              ('name', 'Name'),
                                              ('type', 'Type'),
                                              ('difficulty', 'Difficulty')])

    order = SelectField('Order', choices=[('asc', 'Ascending'),
                                          ('desc', 'Descending')])

    filter_type = SelectField('Filter type', choices=[('all', 'All')])
    filter_difficulty = SelectField('Filter difficulty',
                                    choices=[('all', 'All')])
    submit = SubmitField('Apply')


class AddProblemForm(FlaskForm):
    problem_name = StringField('Problem Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    type = StringField('Type', validators=[DataRequired()])
    default_code = StringField('Default Code', validators=[DataRequired()])
    difficulty = SelectField('Difficulty', choices=[('Easy', 'Easy'),
                                                    ('Medium', 'Medium'),
                                                    ('Hard', 'Hard')])
    submit = SubmitField('Add Problem')


def parse_function_signature(default_code):
    default_code = default_code.removeprefix("def ").removesuffix(":")
    try:
        function_name, function_args = default_code.split("(", 1)
    except ValueError:
        return None
    return function_name, "(" + function_args


def add_problem_tests(session, problem, form):
    test_num = 1
    while True:
        test_input = request.form.get(f'test_input_{test_num}')
        if test_input is None:
            break

        expected_output = request.form.get(f'expected_output_{test_num}')
        test_type = request.form.get(f'test_type_{test_num}')
        try:
            test_data = json.loads(test_input)
        except json.JSONDecodeError:
            form.description.errors.append(
                f"Test case {test_num} must contain valid JSON"
            )
            return False

        session.add(Test(test=test_data, type=test_type,
                         problem_id=problem.problem_id,
                         test_num=test_num, result=expected_output))
        test_num += 1
    return True


def get_problem_tests(problem_id):
    with Session(engine) as session:
        query = select(Problem).where(Problem.problem_id == problem_id)
        problem = session.scalar(query)
        return problem, problem.tests


def build_code_wrapper(code, function_name, indent_code=False):
    if indent_code:
        code = code.replace('\n', '\n    ')
        wrapper = f"""
    import json, sys
    data = json.loads(sys.stdin.read())

    {code}

    result = {function_name}(**data)

    if result is not None:
        print('__RETURN__',  result)
    """
        return wrapper.replace('\n    ', '\n')

    return f"""
import json, sys
data = json.loads(sys.stdin.read())

{code}

result = {function_name}(**data)

if result is not None:
    print('__RETURN__',  result)
"""


def run_test(wrapper, test):
    result = subprocess.run(
        [sys.executable, "-c", wrapper],
        input=json.dumps(test.test),
        capture_output=True, text=True, timeout=5
    )
    output_lines = list(result.stdout.splitlines())
    returned_output = None
    returned_index = None

    if len(output_lines) <= 1000:
        for index, line in enumerate(output_lines):
            if '__RETURN__' in line:
                returned_output = line.removeprefix("__RETURN__ ")
                returned_index = index

    status = 'not returned'
    passed = False
    if returned_index is not None:
        del output_lines[returned_index]
        passed = returned_output == test.result
        status = 'pass' if passed else 'fail'

    return {
        'output': output_lines,
        'error': result.stderr,
        'status': status,
        'type': test.type,
        'testcase': (test.test, test.result),
        'returned_output': returned_output
    }, passed


def save_user_solution(problem_id, code, status, update_status):
    with Session(engine) as session:
        query = select(User_Problem).where(
            User_Problem.problem_id == problem_id,
            User_Problem.user_id == current_user.id
        )
        user_problem = session.scalar(query)
        if user_problem:
            user_problem.solution = code
            if update_status:
                user_problem.status = status
        else:
            session.add(User_Problem(user_id=current_user.id,
                                     problem_id=problem_id,
                                     solution=code, status=status))
        session.commit()


@login_manager.user_loader
def load_user(user_id):
    """this route is used to load the user when they enter each page"""

    query = select(User).where(User.user_id == user_id)
    with Session(engine) as session:
        obj = session.scalar(query)
    return obj


@app.route("/")
def home():
    """redirects the empty route to problem list, the effictive home page"""

    return redirect(url_for("problem_list"))


@app.route('/login', methods=["GET", 'POST'])
def login():
    """this route is responsible for the login page,
    it checks if the users creditntials are correct and
    logs them in or sends them back to the login page to try again"""

    form = LoginForm()
    if form.validate_on_submit():
        with Session(engine) as session:
            query = select(User).where(User.name == form.username.data)
            user = session.scalar(query)

        # check that user credentials do not match the database
        if user is None or not check_password_hash(user.hash,
                                                   form.password.data):
            form.password.errors.append("Username or password failed")
            return render_template("login.html", form=form)

        login_user(user)
        return redirect(url_for("problem_list"))
    return render_template("login.html", form=form)


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """this route is responsible for the signup page,
    it checks if the users creditntials are correct and
    signs them up or sends them back to the signup page to try again"""

    form = SignupForm()
    if form.validate_on_submit():
        with Session(engine) as session:
            query = select(User).where(User.name == form.username.data)
            existing_user = session.scalar(query)
            if existing_user is not None:
                form.username.errors.append("Username is already in use")
                return render_template("signup.html", form=form)

            password_hash = generate_password_hash(form.password.data)

            new_user = User(name=form.username.data,
                            role='normal',
                            hash=password_hash)

            session.add(new_user)
            session.commit()
            login_user(new_user)
        return redirect(url_for("problem_list"))
    return render_template("signup.html", form=form)


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    """this route logs the user out"""

    logout_user()
    return redirect(url_for('login'))


@app.route("/problem/<problem_id>")
@login_required
def problem(problem_id):
    """this route is responsible for the problem page, it recives a
    problem id and then gets the information pertaining to that
    problem, and then sends it to the html to load the problem"""

    with Session(engine) as session:
        q = select(Problem).where(Problem.problem_id == problem_id)
        problem = session.scalar(q)
        if problem is None:
            return redirect(url_for('problem_list'))

        # format the default function that will appear for the problem
        default_text = f"def {problem.function_name}{problem.function_args}:"

        q = select(Test).where(Test.problem_id == problem.problem_id)
        tests = session.scalars(q).all()

        total_tests = len(tests)
        public_tests = len([i for i in tests if i.type == "public"])

        q = select(User_Problem).where(User_Problem.problem_id == problem.problem_id,
                                       User_Problem.user_id == current_user.id)
        user_problem = session.scalar(q)

        code = ''
        if user_problem:
            code = user_problem.solution
            code = code.partition('\n')[2]

    return render_template('problem.html',
                           problem=problem,
                           default_text=default_text,
                           total_tests=total_tests,
                           public_tests=public_tests,
                           code=code)


@app.route('/problem_list', methods=["GET", "POST"])
@login_required
def problem_list():
    """this route is responsible for the problem list page, it gets a list
    of all of the problems and sends their information to the html
    to be rendered, it also handles the filters and sorts for the list"""

    with Session(engine) as session:
        #get list of all problem types
        q = select(Problem.type).distinct().order_by(Problem.type)
        problem_types = session.scalars(q).all()

        # get list of all difficulites
        q = select(Problem.difficulty).distinct().order_by(Problem.difficulty)
        difficulties = session.scalars(q).all()

        # add the types and difficulties as choices for the filters
        form = ProblemListForm()
        form.process(formdata=request.args)
        form.filter_type.choices += [(t, t) for t in problem_types]
        form.filter_difficulty.choices += [(d, d) for d in difficulties]

        # get default values for all inputs
        sort_by = form.sort_by.data or 'problem_id'
        order = form.order.data or 'asc'
        filter_type = form.filter_type.data or 'all'
        filter_difficulty = form.filter_difficulty.data or 'all'

        # associate users input with sqlalchemy statment for sorting
        sort_columns = {'problem_id': Problem.problem_id,
                        'name': Problem.problem_name,
                        'type': Problem.type, 'difficulty': Problem.difficulty}
        sort_column = sort_columns[sort_by]

        # assemble the sqlalchemy query
        q = select(Problem)
        if filter_type != 'all':
            q = q.where(Problem.type == filter_type)
        if filter_difficulty != 'all':
            q = q.where(Problem.difficulty == filter_difficulty)
        if order == 'desc':
            q = q.order_by(sort_column.collate("NOCASE").desc())
        else:
            q = q.order_by(sort_column.collate("NOCASE").asc())

        # create list of problems to send off
        temp_problems = session.scalars(q).all()
        problems = [{'problem_id': i.problem_id,
                     'name': i.problem_name,
                     'difficulty': i.difficulty,
                     'type': i.type} for i in temp_problems]

    return render_template("problem_list.html", problems=problems, form=form)


@app.route('/add_problem', methods=['GET', 'POST'])
@login_required
def add_problem():
    """this route is responsible for the add problem page, it
    receives the information about a proble from the html
    and then adds it to the database, including the testcases"""

    if current_user.role != 'admin':
        return redirect(url_for('problem_list'))

    form = AddProblemForm()
    if form.validate_on_submit():
        problem_name = form.problem_name.data
        description = form.description.data
        type_ = form.type.data
        difficulty = form.difficulty.data
        default_code = form.default_code.data

        signature = parse_function_signature(default_code)
        if signature is None:
            form.default_code.errors.append(
                "Default code must include a function name and arguments"
            )
            return render_template('add_problem.html', form=form)
        function_name, function_args = signature

        with Session(engine) as session:
            new_problem = Problem(problem_name=problem_name,
                                  description=description,
                                  function_name=function_name,
                                  function_args=function_args,
                                  type=type_, difficulty=difficulty)

            session.add(new_problem)
            session.flush()
            if not add_problem_tests(session, new_problem, form):
                return render_template('add_problem.html', form=form)
            session.commit()
        return redirect(url_for('problem_list'))
    return render_template('add_problem.html', form=form)


@app.route('/run_code', methods=['POST'])
def run_code():
    """this route is used for running the users code, it recieves
    the users code and testcases from the problem page and then
    runs the code against the testcases and sends back the results"""

    data = request.get_json()
    code = data['code']
    problem_id = data['problem_id']
    problem, tests = get_problem_tests(problem_id)
    wrapper = build_code_wrapper(code, problem.function_name, indent_code=True)
    response = {'testcases': {}, 'passed': 0}

    for test in tests:
        if test.type == 'private':
            continue
        result, passed = run_test(wrapper, test)
        response['testcases'][test.test_id] = result
        if passed:
            response['passed'] += 1

    return jsonify(response)


@app.route('/submit_code', methods=['POST'])
def submit_code():
    """this route is used for submiting the users code, it recieves
    the users code and testcases from the problem page and then
    runs the code against the testcases and sends back the results"""

    data = request.get_json()
    code = data['code']
    problem_id = data['problem_id']
    problem, tests = get_problem_tests(problem_id)
    wrapper = build_code_wrapper(code, problem.function_name)
    testcase_info = {'testcases': {}, 'passed': 0}

    for test in tests:
        result, passed = run_test(wrapper, test)
        testcase_info['testcases'][test.test_id] = result
        if passed:
            testcase_info['passed'] += 1

    passed_all = testcase_info['passed'] == len(tests)
    status = 'completed' if passed_all else 'attempted'
    save_user_solution(problem_id, code, status, update_status=passed_all)

    submit_info = {'passed': 'Passed' if passed_all else 'Falied'}
    return jsonify({'testcase_info': testcase_info,
                    'submit_info': submit_info})
