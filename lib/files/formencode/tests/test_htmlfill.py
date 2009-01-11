# -*- coding: utf-8 -*-
import sys
import os
import re
import __builtin__
from htmlentitydefs import name2codepoint

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
from formencode import htmlfill
from formencode.doctest_xml_compare import xml_compare
from xml.parsers.expat import ExpatError
from formencode import htmlfill_schemabuilder
try:
    import xml.etree.ElementTree as ET
except ImportError:
    import elementtree.ElementTree as ET

def test_inputoutput():
    data_dir = os.path.join(os.path.dirname(__file__), 'htmlfill_data')
    for fn in os.listdir(data_dir):
        if fn.startswith('data-'):
            fn = os.path.join(data_dir, fn)
            yield run_filename, fn

def run_filename(filename):
    f = open(filename)
    content = f.read()
    f.close()
    parts = re.split(r'---*', content)
    template = parts[0]
    expected = parts[1]
    if len(parts) == 3:
        data_content = parts[2].strip()
    elif len(parts) > 3:
        print parts[3:]
        assert 0, "Too many sections"
    else:
        data_content = ''
    namespace = {}
    if data_content:
        exec data_content in namespace
    data = namespace.copy()
    data['defaults'] = data.get('defaults', {})
    if data.has_key('check'):
        checker = data['check']
        del data['check']
    else:
        def checker(p, s):
            pass
    for name in data.keys():
        if name.startswith('_') or hasattr(__builtin__, name):
            del data[name]
    listener = htmlfill_schemabuilder.SchemaBuilder()
    p = htmlfill.FillingParser(listener=listener, **data)
    p.feed(template)
    p.close()
    output = p.text()
    def reporter(v):
        print v
    try:
        output_xml = ET.XML(output)
        expected_xml = ET.XML(expected)
    except ExpatError:
        comp = output.strip() == expected.strip()
    else:
        comp = xml_compare(output_xml, expected_xml, reporter)
    if not comp:
        print '---- Output:   ----'
        print output
        print '---- Expected: ----'
        print expected
        assert 0
    checker(p, listener.schema())

def test_no_trailing_newline():
    assert (htmlfill.render('<html><body></body></html>', {}, {})
            == '<html><body></body></html>')

def test_escape_defaults():
    rarr = unichr(name2codepoint['rarr'])
    assert (htmlfill.render('<input type="submit" value="next&gt;&rarr;">', {}, {})
            == '<input type="submit" value="next&gt;%s">' % rarr)
    assert (htmlfill.render('<input type="submit" value="1&amp;2">', {}, {})
            == '<input type="submit" value="1&amp;2">')
    assert (htmlfill.render('<input type="submit" value="Japan - &#x65E5;&#x672C; Nihon" />',
                            {}, {}) ==
            u'<input type="submit" value="Japan - 日本 Nihon" />')
    
def test_xhtml():
    result = htmlfill.render('<form:error name="code"/>', errors={'code': 'an error'})
    
def test_trailing_error():
    assert (htmlfill.render('<input type="text" name="email">', errors={'email': 'error'},
                            prefix_error=False)
            == '<input type="text" name="email" class="error" value=""><!-- for: email -->\n<span class="error-message">error</span><br />\n')
    assert (htmlfill.render('<textarea name="content"></textarea>', errors={'content': 'error'},
                            prefix_error=False)
            == '<textarea name="content" class="error"></textarea><!-- for: content -->\n<span class="error-message">error</span><br />\n')
    assert (htmlfill.render('<select name="type"><option value="foo">foo</option></select>', errors={'type': 'error'},
                            prefix_error=False)
            == '<select name="type" class="error"><option value="foo">foo</option></select><!-- for: type -->\n<span class="error-message">error</span><br />\n')

def test_iferror():
    assert (htmlfill.render('<form:iferror name="field1">an error</form:iferror>', errors={}, auto_insert_errors=False)
            == '')
    assert (htmlfill.render('<form:iferror name="field1">an error</form:iferror>', errors={'field1': 'foo'}, auto_insert_errors=False)
            == 'an error')
    assert (htmlfill.render('<form:iferror name="not field1">no errors</form:iferror>', errors={}, auto_insert_errors=False)
            == 'no errors')
    assert (htmlfill.render('<form:iferror name="not field1">no errors</form:iferror>', errors={'field1': 'foo'}, auto_insert_errors=False)
            == '')
    assert (htmlfill.render('<form:iferror name="field1">errors</form:iferror><form:iferror name="not field1">no errors</form:iferror>',
                            errors={}, auto_insert_errors=False)
            == 'no errors')
    assert (htmlfill.render('<form:iferror name="field1">errors</form:iferror><form:iferror name="not field1">no errors</form:iferror>',
                            errors={'field1': 'foo'}, auto_insert_errors=False)
            == 'errors')

def test_literal():
    assert (htmlfill.render('<form:error name="foo" />',
                            errors={'foo': htmlfill.htmlliteral('<test>')})
            == '<span class="error-message"><test></span><br />\n')

def test_image_submit():
    assert (htmlfill.render('<input name="image-submit" type="image" src="foo.jpg" value="bar">',
                            defaults={'image-submit': 'blahblah'})
            == '<input name="image-submit" type="image" src="foo.jpg" value="bar">')

def test_unicode():
    assert (htmlfill.render(u'<input type="checkbox" name="tags" value="2" />',
                           dict(tags=[])) == 
            '<input type="checkbox" name="tags" value="2" />')
