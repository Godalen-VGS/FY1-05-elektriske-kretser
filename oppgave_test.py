"""Automatisk retting av FY1-05-elektriske-kretser.

Hver sjekk i SJEKKER er én deltest, og poengene fordeles likt på dem.
De samme sjekkene ligger i "Test løsningen din"-cellen nederst i notebooken.
"""
import pytest

from notebook_loader import last_notebook

def naer(a, b, rel=1e-3):
    """Sant hvis tallet a er innenfor rel (relativt) av b."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) <= rel * abs(b)


def S(tekst):
    """Gjør tekst om til et sympy-uttrykk, f.eks. S("x**2 - 1")."""
    import sympy
    return sympy.sympify(tekst, locals={n: sympy.Symbol(n) for n in ("N", "O", "Q", "S")})


def lik(a, b):
    """Sant hvis a og b er matematisk like.

    Lister og mengder sammenlignes uten hensyn til rekkefølge, tupler (koordinater) i rekkefølge.
    """
    import sympy
    if a is None:
        return False
    if isinstance(b, tuple):
        if not isinstance(a, (tuple, list, sympy.Tuple)) or len(a) != len(b):
            return False
        return all(lik(x, y) for x, y in zip(a, b))
    if isinstance(b, (list, set)):
        if isinstance(a, sympy.FiniteSet):
            a = list(a)
        if not isinstance(a, (list, tuple, set)) or len(a) != len(b):
            return False
        rest = list(a)
        for y in b:
            for i, x in enumerate(rest):
                if lik(x, y):
                    del rest[i]
                    break
            else:
                return False
        return True
    if isinstance(b, dict):
        if not isinstance(a, dict) or len(a) != len(b):
            return False
        a = {str(k): v for k, v in a.items()}
        return all(str(k) in a and lik(a[str(k)], v) for k, v in b.items())
    try:
        a, b = sympy.sympify(a), sympy.sympify(b)
    except (sympy.SympifyError, TypeError):
        return False
    vanlige = lambda u: u.subs({s: sympy.Symbol(s.name) for s in u.free_symbols})
    a, b = vanlige(a), vanlige(b)
    if isinstance(a, sympy.Set) or isinstance(b, sympy.Set):
        return a == b
    if getattr(b, "is_Relational", False):
        return a == b
    try:
        return sympy.simplify(a - b) == 0
    except TypeError:
        return a == b

oppgave = last_notebook("oppgave")

SJEKKER = [
    ('1_serie', 'serie([2, 3, 5]) skal gi 10', 'naer(serie([2, 3, 5]), 10)'),
    ('1_parallell', 'parallell([6, 12]) skal gi 4', 'naer(parallell([6, 12]), 4) and naer(parallell([10, 10, 10]), 10/3)'),
    ('2', 'I_tot, I_2 og I_3 skal være 1.5 A, 1.0 A og 0.5 A', 'naer(I_tot, 1.5) and naer(I_2, 1) and naer(I_3, 0.5)'),
    ('3', 'strommer skal være I1 = 21/11 A, I2 = -6/11 A og I3 = 15/11 A', "lik(strommer, {'I1': S('21/11'), 'I2': S('-6/11'), 'I3': S('15/11')})"),
    ('4', 'effekt_motstand(4, 1.5) skal gi 9 W', 'naer(effekt_motstand(4, 1.5), 9) and naer(effekt_motstand(100, 0.1), 1)'),
    ('5_lik', 'belastet_deler(12, 1000, 1000, 1000) skal gi 4 V', 'naer(belastet_deler(12, 1000, 1000, 1000), 4)'),
    ('5_stor_last', 'belastet_deler med svært stor last skal nærme seg 6 V', 'naer(belastet_deler(12, 1000, 1000, 1e12), 6, rel=1e-6)'),
]


@pytest.mark.parametrize(
    "beskrivelse,uttrykk", [s[1:] for s in SJEKKER], ids=[s[0] for s in SJEKKER]
)
def test_sjekk(beskrivelse, uttrykk):
    navnerom = {**vars(oppgave), "naer": naer, "lik": lik, "S": S}
    assert eval(uttrykk, navnerom), beskrivelse
