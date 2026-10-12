"""Bridge translations to the vendor module without editing its source."""

from odoo.tools.misc import ReadonlyDict
from odoo.tools.translate import CodeTranslations


_VENDOR_MODULE = "hotel_management_odoo"
_LOCAL_MODULE = "poliedro_hotel_es_co"


def post_load_hook():
    """Merge this addon's es_CO code terms into the vendor module namespace."""
    if getattr(CodeTranslations, "_poliedro_hotel_es_co_patched", False):
        return

    original_python_loader = CodeTranslations._load_python_translations
    original_web_loader = CodeTranslations._load_web_translations

    def load_python_translations(self, module_name, lang):
        original_python_loader(self, module_name, lang)
        if module_name == _VENDOR_MODULE:
            target = (module_name, lang)
            translations = dict(self.python_translations[target])
            translations.update(
                CodeTranslations._get_code_translations(
                    _LOCAL_MODULE,
                    lang,
                    lambda row: row.get("value")
                    and "odoo-python" in row["comments"],
                )
            )
            self.python_translations[target] = ReadonlyDict(translations)

    def load_web_translations(self, module_name, lang):
        original_web_loader(self, module_name, lang)
        if module_name == _VENDOR_MODULE:
            target = (module_name, lang)
            messages = {
                message["id"]: message["string"]
                for message in self.web_translations[target]["messages"]
            }
            local_messages = CodeTranslations._get_code_translations(
                _LOCAL_MODULE,
                lang,
                lambda row: row.get("value")
                and "odoo-javascript" in row["comments"],
            )
            messages.update(local_messages)
            self.web_translations[target] = ReadonlyDict(
                {
                    "messages": tuple(
                        ReadonlyDict({"id": source, "string": value})
                        for source, value in messages.items()
                    )
                }
            )

    CodeTranslations._load_python_translations = load_python_translations
    CodeTranslations._load_web_translations = load_web_translations
    CodeTranslations._poliedro_hotel_es_co_patched = True

    # A long-running worker may have loaded the vendor dictionaries already.
    translator = __import__("odoo.tools.translate", fromlist=["code_translations"])
    for cache_name in ("python_translations", "web_translations"):
        cache = getattr(translator.code_translations, cache_name)
        for key in tuple(cache):
            if key[0] == _VENDOR_MODULE:
                cache.pop(key, None)
