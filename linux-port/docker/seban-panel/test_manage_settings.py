"""Run against staged app.py; every POST uses an isolated spool and mocked DB."""
import tempfile
from pathlib import Path
from unittest.mock import patch
import app as panel

panel.app.config['TESTING'] = True
with tempfile.TemporaryDirectory() as tmp, patch.object(panel,'RATES_SPOOL',Path(tmp)), \
     patch.object(panel,'AI_WEIGHTS_FILE',Path(tmp) / 'playerbot_weights.tsv'), \
     patch.object(panel,'settings',return_value={'setup_complete':'1','auth_enabled':'0'}), \
     patch.object(panel,'db',side_effect=AssertionError('POST must not write the DB')):
    client=panel.app.test_client()
    form={'submit_action':'apply','exp':'150','drop':'170','yang':'190','map_21':'1','map_stone_21':'350','map_1':''}
    assert client.post('/manage/restart-config',data=form).status_code==302
    # The game container watches `request' and nothing else; the old
    # server-settings.request was read by nobody and deleted by nobody.
    request=Path(tmp)/'request'; original=request.read_text()
    assert 'exp=150' in original and 'drop=170' in original and 'yang=190' in original
    assert not (Path(tmp)/'server-settings.request').exists()
    # A restart already under way is refused, and the refusal expires.
    assert client.post('/manage/restart-config',data=form).status_code==302
    assert request.read_text()==original
    (Path(tmp)/'rates.status').write_text('state=ok\ntime=1\n')
    for key,value in [('map_stone_21','0'),('map_21','3601'),('exp','not-a-number')]:
        invalid=dict(form);invalid[key]=value
        request.unlink(missing_ok=True)
        assert client.post('/manage/restart-config',data=invalid).status_code==302
        assert not request.exists()
    with patch.object(panel,'read_rates',return_value={'exp':111,'drop':112,'yang':113}):
        assert client.post('/manage/restart-config',data={'submit_action':'restart'}).status_code==302
    assert 'exp=111' in request.read_text()
    request.unlink(); (Path(tmp)/'rates.status').unlink()
    (Path(tmp)/'map-regens.status').write_text('state=ok\nmap_21=1\nmap_stone_21=350\n')
    status=panel.read_map_regen_status()
    assert status['values']=={21:'1'} and status['stones']=={21:'350'}
    weights_file=Path(tmp)/'playerbot_weights.tsv'
    weights_file.write_text('BOOKS\t0\nCHEST\t10\nCHEST_STONE\t300\nFUTURE_KEY\t77\n')
    weights=panel.read_ai_weights()
    assert weights['BOOKS']==0 and weights['CHEST']==10 and weights['CHEST_STONE']==300
    weights['BOOKS']=1; weights['CHEST']=11; weights['CHEST_STONE']=301
    panel.write_ai_weights(weights)
    saved=weights_file.read_text()
    assert 'BOOKS\t1' in saved and 'CHEST\t11' in saved and 'CHEST_STONE\t301' in saved and 'FUTURE_KEY\t77' in saved
    assert panel.SKILLS[(0,1)][3] == (4, 'Aura Miecza') and len(panel.SKILLS[(0,1)]) == 5
    # Tieru ships master icons as *_m.png for M/G/P; *_p.png does not exist.
    skill_bytes=bytes(24) + bytes([3, 35])
    assert panel.parse_skills(skill_bytes, 0, 1)[0]['icon_suffix'] == '_m'
    assert panel.MAP_NAMES[61] == 'Góra Sohan' and panel.MAP_NAMES[104] == 'Loch Pająków V1'
    assert panel.MAP_NAMES[108] == 'Loch Małp Normalny' and panel.MAP_NAMES[109] == 'Loch Małp Trudny'
    assert panel.MAP_BOUNDS[61] == (358400, 153600, 153600, 153600)
    assert 61 in panel.MAP_STONE_RESPAWN_IDS and not {25, 104, 108, 109} & panel.MAP_STONE_RESPAWN_IDS
    assert [index for index, _name in panel.TRACKED_MAP_OPTIONS] == [21, 23, 24, 25, 61, 63, 64, 104, 108, 109, 65]
    assert panel.changelog_entries()[0]['version'] == '1.37.2'
    with patch.object(panel, 'rows', return_value=[]) as ranking_rows:
        assert panel.bot_ranking('bosses') == []
        assert "BOSS_KILL" in ranking_rows.call_args.args[0]
    with patch.object(panel,'live_map_counts',return_value=[]), patch.object(panel,'live_bots',return_value=[]), \
         patch.object(panel,'read_rates',return_value={'exp':150,'drop':170,'yang':190}), \
         patch.object(panel,'restart_progress',return_value={'state':'ok','percent':100,'stage':'Serwer działa'}), \
         patch.object(panel,'globals_for_templates'):
        # Use real Jinja rendering with context processors disabled (all DB mocked).
        processors=panel.app.template_context_processors[None]
        panel.app.template_context_processors[None]=[]
        try:
            response=client.get('/manage')
            assert response.status_code==200
            html=response.get_data(as_text=True)
            assert 'id="map_stone_21"' in html and 'formnovalidate' in html
            assert html.count('id="restart-fill"')==1 and 'Chunjo M1 — Joan' in html
            assert html.index('restart-console') < html.index('id="restart-fill"')
        finally:panel.app.template_context_processors[None]=processors
    assert client.get('/changelog').status_code == 200
print('PASS: Flask batch validation, weights incl. BOOKS/CHEST and forward-compatible preservation, skills, queue and manage rendering')
