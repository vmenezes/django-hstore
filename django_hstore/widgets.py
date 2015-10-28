from __future__ import unicode_literals, absolute_import

from django import forms
from django.contrib.admin.widgets import AdminTextareaWidget
from django.contrib.admin.templatetags.admin_static import static
from django.template import Context
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.conf import settings


__all__ = [
    'AdminHStoreWidget'
]


class BaseAdminHStoreWidget(AdminTextareaWidget):
    """
    Base admin widget class for default-admin and grappelli-admin widgets
    """
    admin_style = 'default'

    @property
    def media(self):
        internal_js = [
            "django_hstore/underscore-min.js",
            "django_hstore/hstore-widget.js"
        ]

        js = [static("admin/js/%s" % path) for path in internal_js]

        return forms.Media(js=js)


    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        # it's called "original" because it will be replaced by a copy
        attrs['class'] = 'hstore-original-textarea'

        # get default HTML from AdminTextareaWidget
        html = super(BaseAdminHStoreWidget, self).render(name, value, attrs)

        # prepare template context
        template_context = Context({
            'field_name': name,
            'STATIC_URL': settings.STATIC_URL
        })
        # get template object
        template = get_template('hstore_%s_widget.html' % self.admin_style)
        # render additional html
        additional_html = template.render(template_context)

        # append additional HTML and mark as safe
        html = html + additional_html
        html = mark_safe(html)

        return html
    

from django.forms.widgets import flatatt
import json


class HStoreKeyValueInput(forms.Widget):
    def __init__(self, *args, **kwargs):
        self.key_attrs = {}
        self.val_attrs = {}
        if "key_attrs" in kwargs:
            self.key_attrs = kwargs.pop("key_attrs")
        if "val_attrs" in kwargs:
            self.val_attrs = kwargs.pop("val_attrs")
        forms.Widget.__init__(self, *args, **kwargs)
        
    def render(self, name, value, attrs=None):
        if value is None:
            value = '{}'
        if type(value) == dict:
            twotuple = value
        else:
            twotuple = json.loads(value)
            
        ret = ''
        npt_html = '<input type="text" name="json_key[%(fieldname)s]" value="%(key)s" %(key_attrs)s> <input type="text" name="json_value[%(fieldname)s]" value="%(value)s" %(val_attrs)s><br />'
        if value and len(value) > 0:
            for k,v in twotuple.items():
                ctx = {'key':k,
                       'value':v,
                       'fieldname':name,
                       'key_attrs': flatatt(self.key_attrs),
                       'val_attrs': flatatt(self.val_attrs) }
                ret += npt_html % ctx
        
        ctx = {'key': '',
               'value': '',
               'fieldname':name,
               'key_attrs': flatatt(self.key_attrs),
               'val_attrs': flatatt(self.val_attrs) }
        new_input = npt_html % ctx
        ret += new_input
        
        ret += '<button id="btnNewKeyValue">New Key/Value</button>'
        ret += '''
        <script>
        django.jQuery("#btnNewKeyValue").on("click", function(e){{
            e.preventDefault();
            django.jQuery('{}').insertBefore(this);
        }})
        </script>
        '''.format(new_input)
        return mark_safe(ret)
        
    def value_from_datadict(self, data, files, name):
        keys = data.getlist("json_key[{}]".format(name))
        values = data.getlist("json_value[{}]".format(name))
        if keys and values:
            data_dict = {}
            for key, value in zip(keys, values):
                if len(key) > 0:
                    data_dict[key] = value
            print(data_dict)
            jsontext = json.dumps(data_dict)
        return jsontext


class DefaultAdminHStoreWidget(HStoreKeyValueInput):
    """
    Widget that displays the HStore contents
    in the default django-admin with a nice interactive UI
    """
    admin_style = 'default'


class GrappelliAdminHStoreWidget(BaseAdminHStoreWidget):
    """
    Widget that displays the HStore contents
    in the django-admin with a nice interactive UI
    designed for django-grappelli
    """
    admin_style = 'grappelli'


if 'grappelli' in settings.INSTALLED_APPS:
    AdminHStoreWidget = GrappelliAdminHStoreWidget
else:
    AdminHStoreWidget = DefaultAdminHStoreWidget
