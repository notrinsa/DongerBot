
class Colors:

    def __init__(self):
        pass

    _bold = "\x02"
    _italic = "\x1D"
    _underline = "\x1F"
    colorize = "\x03"

    blanc = '00'
    noir = '01'
    bleu = '02'
    vert = '03'
    rouge = '04'
    marron = '05'
    violet = '06'
    orange = '07'
    jaune = '08'
    citron = '09'
    teal = '10'
    cyan = '11'
    royal = '12'
    rose = '13'
    gris = '14'
    argent = '15'

    def write_color(self, **kwargs):
        if 'message' not in kwargs:
            return False

        args = kwargs['message'].split()
        # Prefix
        prefix = self.colorize
        # Foreground
        if 'fg' in kwargs and kwargs['fg'] is not None and hasattr(self, kwargs['fg']):
            prefix += getattr(self, kwargs['fg'])
        # Background
        if 'bg' in kwargs and kwargs['bg'] is not None and hasattr(self, kwargs['bg']):
            if kwargs['fg'] is None:
                prefix += getattr(self, "noir")
            prefix += "," + getattr(self, kwargs['bg'])

        return prefix + kwargs['message']

    def _b(self, string):
        return self._bold + string

    def _i(self, string):
        return self._italic + string

    def _u(self, string):
        return self._underline + string

    @staticmethod
    def liste():
        return "Couleurs disponibles: blanc, noir, " \
               "bleu, vert, rouge, marron, violet, orange, " \
               "jaune, citron, teal, cyan, royal, rose, gris, argent"







