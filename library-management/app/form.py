from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError


class RegisterForm(FlaskForm):
    username = StringField(label='用户名', validators=[DataRequired(), Length(1, 80)])
    password = PasswordField(label='密码', validators=[DataRequired(), Length(1, 128)])
    password2 = PasswordField(label='确认密码', validators=[DataRequired(), Length(1, 128)])
    email = StringField(label='邮箱', validators=[DataRequired(), Length(1, 120)])
    submit = SubmitField(label='注册')

    def validate_password2(self, field):
        if self.password.data != field.data:
            raise ValidationError('两次输入的密码不一致，请重新输入')

class LoginForm(FlaskForm):
    username = StringField(label='用户名', validators=[DataRequired(), Length(1, 80)])
    password = PasswordField(label='密码', validators=[DataRequired(), Length(1, 128)])
    submit = SubmitField(label='登录')

class RetrievePasswordForm(FlaskForm):
    email = StringField(label='邮箱', validators=[DataRequired(), Length(1, 120)])
    captcha = StringField(label='图形验证码', validators=[DataRequired(), Length(4, 4)])
    verification_code = StringField(label='邮箱验证码', validators=[])
    password = PasswordField(label='新密码', validators=[])
    password2 = PasswordField(label='确认新密码', validators=[])
    submit = SubmitField(label='重置密码')
