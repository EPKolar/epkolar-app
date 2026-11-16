# -*- coding: utf-8 -*-
"""v3.9.1020 Samsung-Hell: App 'Hell' + Handy-Nachtmodus wurde am A55 dunkel (28,30,28 gemessen 16.11.).
Die Thema-Marke data-epk-thema folgt der App-Wahl (fruehes Skript + Thema-Wechsel); eine statische
CSS-Regel bestaetigt bei Geraete-Dunkel die Wahl Hell. Die Wahl selbst liest das Geraet nie."""

REGEL = ':root[data-epk-thema="hell"] { color-scheme: only light; background-color: #F2F4F2; }'


def test_marke_im_fruehen_skript(index_html):
    kopf = index_html[:index_html.index("</script>")]
    assert 'document.documentElement.setAttribute("data-epk-thema",d?"dunkel":"hell");' in kopf


def test_marke_beim_themawechsel(index_html):
    assert ('document.documentElement.style.colorScheme=dark?"only dark":"only light";'
            'document.documentElement.setAttribute("data-epk-thema",dark?"dunkel":"hell");') in index_html


def test_regel_steht_einmal_und_nur_fuer_hell(index_html):
    assert index_html.count(REGEL) == 1
    assert 'data-epk-thema="dunkel"' not in index_html.split("</style>")[0]


def test_umkehrprobe(index_html):
    assert REGEL not in index_html.replace(REGEL, "", 1)
