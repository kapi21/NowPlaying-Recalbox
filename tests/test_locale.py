import os
import tempfile
import time
import unittest

from np.locale import normalize_lang, read_system_language, resolve_lang, reset_lang_cache


class TestNormalizeLang(unittest.TestCase):
    def test_es_es(self):
        self.assertEqual(normalize_lang('es_ES'), 'es')

    def test_en_us(self):
        self.assertEqual(normalize_lang('en_US'), 'en')

    def test_unsupported_falls_to_en(self):
        self.assertEqual(normalize_lang('fr_FR'), 'en')
        self.assertEqual(normalize_lang('zh_CN'), 'en')

    def test_empty_falls_to_en(self):
        self.assertEqual(normalize_lang(None), 'en')
        self.assertEqual(normalize_lang(''), 'en')
        self.assertEqual(normalize_lang('  '), 'en')

    def test_bare_code(self):
        self.assertEqual(normalize_lang('es'), 'es')
        self.assertEqual(normalize_lang('EN'), 'en')


class TestReadSystemLanguage(unittest.TestCase):
    def test_reads_key(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, 'recalbox.conf')
            with open(p, 'w', encoding='utf-8') as f:
                f.write(';system.language=en_US\nsystem.language=es_ES\n')
            self.assertEqual(read_system_language(p), 'es_ES')

    def test_missing_file(self):
        self.assertIsNone(read_system_language('/no/such/recalbox.conf'))

    def test_commented_only(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, 'recalbox.conf')
            with open(p, 'w', encoding='utf-8') as f:
                f.write(';system.language=fr_FR\n')
            self.assertIsNone(read_system_language(p))


class TestResolveLang(unittest.TestCase):
    def setUp(self):
        reset_lang_cache()
        self._old = os.environ.pop('NP_LANG', None)

    def tearDown(self):
        reset_lang_cache()
        if self._old is not None:
            os.environ['NP_LANG'] = self._old
        else:
            os.environ.pop('NP_LANG', None)

    def test_np_lang_override(self):
        os.environ['NP_LANG'] = 'en'
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, 'recalbox.conf')
            with open(p, 'w', encoding='utf-8') as f:
                f.write('system.language=es_ES\n')
            self.assertEqual(resolve_lang(conf_path=p), 'en')

    def test_from_conf(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, 'recalbox.conf')
            with open(p, 'w', encoding='utf-8') as f:
                f.write('system.language=es_ES\n')
            self.assertEqual(resolve_lang(conf_path=p), 'es')

    def test_cache(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, 'recalbox.conf')
            with open(p, 'w', encoding='utf-8') as f:
                f.write('system.language=es_ES\n')
            self.assertEqual(resolve_lang(conf_path=p, cache_ttl=60), 'es')
            with open(p, 'w', encoding='utf-8') as f:
                f.write('system.language=en_US\n')
            # still cached
            self.assertEqual(resolve_lang(conf_path=p, cache_ttl=60), 'es')
            reset_lang_cache()
            self.assertEqual(resolve_lang(conf_path=p, cache_ttl=60), 'en')


if __name__ == '__main__':
    unittest.main()
