from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired,URL


class SubForm(FlaskForm):
    website = StringField('site', validators=[DataRequired(),URL()])
    submit = SubmitField('获取数据')


class DefaultForm(FlaskForm):
    submit_default = SubmitField('默认爬取')
