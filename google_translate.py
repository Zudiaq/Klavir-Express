from translate import Translator

def translate_to_persian(text):
    """
    Translate the given text to Persian (Farsi).
    Args:
        text (str): The text to translate.
    Returns:
        str: Translated text in Persian, or None if translation fails.
    """
    TRANSLATE_TO_LANGUAGE = "fa"  # Persian
    try:
        translator = Translator(to_lang=TRANSLATE_TO_LANGUAGE)
        result = translator.translate(text)
        # Remove unwanted characters like numbers and hashtags
        result = ''.join(filter(lambda x: not x.isdigit() and x not in ['#', '&', ';'], result))
        return result
    except Exception as e:
        print(f"Error translating text: {e}")
        return None
