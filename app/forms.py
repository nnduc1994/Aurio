from flask_wtf import Form
from wtforms import StringField, SubmitField, validators, PasswordField, BooleanField, SelectField, RadioField


class LoginForm(Form):
    user_name = StringField("username", [validators.DataRequired("Please enter user name!")])
    password = PasswordField("password", [validators.DataRequired("Please enter password!")])
    remember_me = BooleanField("remember me", default=False)
    login = SubmitField("Log in")


class CreateKeyForm(Form):
    key_number = StringField("keynumber", [validators.DataRequired("Please enter key number!")])
    selected_company = SelectField("company")


class SearchForm(Form):
    key_input = StringField("input")


class CreateCompanyForm(Form):
    company_name = StringField("companyname", [validators.DataRequired("Please enter company name!")])


class CreateUserForm(Form):
    user_name = StringField("username", [validators.DataRequired("Please input something")])
    name = StringField("name", [validators.DataRequired("Please input something")])
    role = RadioField('Role', choices=[(1, 'Normal User'), ('2', 'Company Admin')])
    password = StringField("input", [validators.DataRequired("Please input something")])

    selected_company = SelectField("company")


class RemoveUserForm(Form):
    selected_user = SelectField('user')


