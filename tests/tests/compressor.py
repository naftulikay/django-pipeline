# -*- coding: utf-8 -*-
import base64

from mock import patch

from django.test import TestCase

from pipeline.conf import settings
from pipeline.compressors import Compressor
from pipeline.compressors.yui import YUICompressor


class CompressorTest(TestCase):
    def setUp(self):
        self.compressor = Compressor()
        self.old_pipeline_url = settings.PIPELINE_URL
        self.old_pipeline_root = settings.PIPELINE_ROOT
        settings.PIPELINE_URL = 'http://localhost/static/'

    def test_js_compressor_class(self):
        self.assertEquals(self.compressor.js_compressor, YUICompressor)

    def test_css_compressor_class(self):
        self.assertEquals(self.compressor.css_compressor, YUICompressor)

    def test_concatenate_and_rewrite(self):
        css = self.compressor.concatenate_and_rewrite([
            'css/first.css',
            'css/second.css'
        ])
        self.assertEquals(""".concat {\n  display: none;\n}\n.concatenate {\n  display: block;\n}""", css)

    def test_concatenate(self):
        js = self.compressor.concatenate([
            'js/first.js',
            'js/second.js'
        ])
        self.assertEquals("""function concat() {\n  console.log(arguments);\n}\nfunction cat() {\n  console.log("hello world");\n}""", js)

    @patch.object(base64, 'b64encode')
    def test_encoded_content(self, mock):
        self.compressor.encoded_content('images/arrow.png')
        self.assertTrue(mock.called)
        mock.reset_mock()
        self.compressor.encoded_content('images/arrow.png')
        self.assertFalse(mock.called)

    def test_relative_path(self):
        settings.PIPELINE_ROOT = '/var/www/static/'
        relative_path = self.compressor.relative_path('/var/www/static/images/sprite.png')
        self.assertEquals(relative_path, '/images/sprite.png')

    def test_absolute_path(self):
        absolute_path = self.compressor.absolute_path('../../images/sprite.png',
            'css/plugins/gallery.css')
        self.assertEquals(absolute_path, 'images/sprite.png')
        absolute_path = self.compressor.absolute_path('/images/sprite.png',
            'css/plugins/gallery.css')
        self.assertEquals(absolute_path, '/images/sprite.png')

    def test_template_name(self):
        name = self.compressor.template_name('templates/photo/detail.jst',
            'templates/')
        self.assertEquals(name, 'photo_detail')
        name = self.compressor.template_name('templates/photo_edit.jst', '')
        self.assertEquals(name, 'photo_edit')

    def test_embeddable(self):
        self.assertFalse(self.compressor.embeddable('images/sprite.png', None))
        self.assertFalse(self.compressor.embeddable('images/arrow.png', 'datauri'))
        self.assertTrue(self.compressor.embeddable('images/embed/arrow.png', 'datauri'))
        self.assertFalse(self.compressor.embeddable('images/arrow.dat', 'datauri'))

    def test_construct_asset_path(self):
        asset_path = self.compressor.construct_asset_path("../../images/sprite.png",
            "css/plugins/gallery.css")
        self.assertEquals(asset_path, "http://localhost/static/images/sprite.png")
        asset_path = self.compressor.construct_asset_path("/images/sprite.png",
            "css/plugins/gallery.css")
        self.assertEquals(asset_path, "http://localhost/static/images/sprite.png")

    def test_url_rewrite(self):
        self.maxDiff = None
        output = self.compressor.concatenate_and_rewrite([
            'css/urls.css',
        ])
        self.assertMultiLineEqual("""@font-face {
  font-family: 'Pipeline';
  src: url(http://localhost/static/fonts/pipeline.eot);
  src: url(http://localhost/static/fonts/pipeline.eot?#iefix) format('embedded-opentype');
  src: local('☺'), url(http://localhost/static/fonts/pipeline.woff) format('woff'), url(http://localhost/static/fonts/pipeline.ttf) format('truetype'), url(http://localhost/static/fonts/pipeline.svg#IyfZbseF) format('svg');
  font-weight: normal;
  font-style: normal;
}
.relative-url {
  background-image: url(http://localhost/static/images/sprite-buttons.png);
}
.absolute-url {
  background-image: url(http://localhost/static/images/sprite-buttons.png);
}
.absolute-full-url {
  background-image: url(http://localhost/images/sprite-buttons.png);
}
.no-protocol-url {
  background-image: url(//images/sprite-buttons.png);
}""", output)

    def tearDown(self):
        settings.PIPELINE_URL = self.old_pipeline_url
        settings.PIPELINE_ROOT = self.old_pipeline_root
