from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


# todo 便签注释 wtf
class SubForm(FlaskForm):
    # Radio Box类型，单选框，choices里的内容会在ul标签里，里面每个项是(值，显示名)对
    # gender = RadioField('Gender', choices=[('m', 'Male'), ('f', 'Female')], validators=[DataRequired()])
    website = StringField('site', validators=[DataRequired()])
    submit = SubmitField('获取数据')


class DefaultForm(FlaskForm):
    submit_default = SubmitField('默认爬取')
