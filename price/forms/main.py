from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, EmailField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class ContatoForm(FlaskForm):
    nome = StringField('Nome', validators=[
                       DataRequired(), Length(min=3, max=100)])
    email = EmailField('E-mail', validators=[DataRequired(), Email()])
    mensagem = TextAreaField('Mensagem', validators=[
                             DataRequired(), Length(min=10)])
    submit = SubmitField('Enviar Mensagem')


class LoginForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')


class SignUpForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    confirmar_senha = PasswordField('Confirmar Senha', validators=[
        DataRequired(),
        EqualTo('senha', message='As senhas devem ser iguais.')
    ])
    submit = SubmitField('Criar Conta')
