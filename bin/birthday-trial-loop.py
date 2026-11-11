#!/usr/bin/env python3
"""Private metrics snapshots and guarded manual trial publishing for birthday tests."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / '.work/birthday-bowling/loop'
USER_ID = os.environ['IG_USER_ID']
ACCOUNT = os.environ.get('IG_ACCOUNT', 'your_handle')
BASELINES = ['18006667874992265', '17873955555635617']
METRICS = ['views', 'reach', 'likes', 'comments', 'saved', 'shares',
           'total_interactions', 'ig_reels_avg_watch_time']


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.chmod(0o600)
    temporary.replace(path)


def api(path, **params):
    token = subprocess.check_output([
        'security', 'find-generic-password', '-a', ACCOUNT,
        '-s', 'com.video-edits.instagram-access-token', '-w'
    ], stderr=subprocess.DEVNULL).decode().strip()
    url = 'https://graph.instagram.com/v26.0/' + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        details = json.loads(error.read()).get('error', {})
        raise RuntimeError(f"Instagram {error.code}: {details.get('message', 'request failed')}") from None


def recent():
    posts, cursor = [], None
    for _ in range(20):
        params = {'fields': 'id,caption,timestamp,permalink,media_type', 'limit': 100}
        if cursor:
            params['after'] = cursor
        result = api(USER_ID + '/media', **params)
        posts.extend(result.get('data', []))
        paging = result.get('paging', {})
        if not paging.get('next'):
            break
        cursor = paging.get('cursors', {}).get('after')
        if not cursor:
            break
    return posts


def snapshot():
    posts = recent()
    by_id = {p['id']: p for p in posts}
    ids = set(BASELINES)
    for receipt in (STATE / 'attempts').glob('*.json'):
        item = json.loads(receipt.read_text())
        if item.get('media_id'):
            ids.add(item['media_id'])
    results = []
    for ident in sorted(ids):
        item = by_id.get(ident) or api(ident, fields='id,caption,timestamp,permalink')
        item['metrics'] = {}
        try:
            metrics = api(ident + '/insights', metric=','.join(METRICS))
            for metric in metrics.get('data', []):
                values = metric.get('values', [])
                item['metrics'][metric['name']] = values[-1]['value'] if values else None
        except RuntimeError as error:
            item['metrics_error'] = str(error)
        results.append(item)
    report = {'observed_at': now(), 'account': ACCOUNT, 'recent_media': posts, 'experiments': results}
    dest = STATE / 'snapshots' / (dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.json')
    save(dest, report)
    print(json.dumps({'snapshot': str(dest), 'experiments': results}, indent=2))


def publish(queue, authorized_extra_batch=False, authorized_birthday_six=False, authorized_music_refresh=False):
    queue = Path(queue).resolve()
    queue.relative_to(ROOT / 'publishing/queue')
    meta = json.loads((queue / 'publish.json').read_text())
    if (meta.get('account'), meta.get('format'), meta.get('graduation_strategy')) != (ACCOUNT, 'trial_reel', 'MANUAL'):
        raise RuntimeError('Refusing anything except your_handle manual graduation trial reels')
    subprocess.run([str(ROOT / 'bin/validate-instagram-reel.sh'), str(queue)], check=True)
    identity = api(USER_ID, fields='id,username')
    if identity.get('username') != ACCOUNT:
        raise RuntimeError('Account identity did not match')
    caption = (queue / 'caption.txt').read_text().strip()
    if any(p.get('caption', '').strip() == caption for p in recent()):
        raise RuntimeError('Matching caption already exists on Instagram; reconcile before retrying')
    with (queue / 'reel.mp4').open('rb') as handle:
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    folder = STATE / 'attempts'
    folder.mkdir(parents=True, exist_ok=True)
    attempts_today = 0
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=24)
    for path in folder.glob('*.json'):
        prior = json.loads(path.read_text())
        if prior.get('sha256') == digest or prior.get('queue') == str(queue):
            raise RuntimeError('Prior attempt found; inspect its receipt and Instagram before retrying')
        if dt.datetime.fromisoformat(prior['started_at']) > cutoff:
            attempts_today += 1
    extra_allowed = (authorized_extra_batch and
                     dt.datetime.now(dt.timezone.utc).date().isoformat() == '2026-09-14' and
                     queue.name in {'birthday-cake-priorities-trial', 'birthday-my-people-trial'})
    if authorized_extra_batch and not extra_allowed:
        raise RuntimeError('Extra batch authorization does not cover this queue or date')
    six_allowed = (authorized_birthday_six and
                   dt.datetime.now(dt.timezone.utc).date().isoformat() == '2026-09-14' and
                   queue.name in {'birthday-full-roll-trial', 'birthday-main-character-trial',
                                  'birthday-accessories-trial', 'birthday-cake-reveal-trial',
                                  'birthday-wish-list-trial', 'birthday-camera-roll-trial'})
    if authorized_birthday_six and not six_allowed:
        raise RuntimeError('Six reel authorization does not cover this queue or date')
    music_allowed = (authorized_music_refresh and
                     dt.datetime.now(dt.timezone.utc).date().isoformat() == '2026-09-14' and
                     queue.name in {'birthday-indian-home-trial', 'birthday-flip-camera-trial', 'birthday-indian-home-clean-trial'})
    if authorized_music_refresh and not music_allowed:
        raise RuntimeError('Music refresh authorization does not cover this queue or date')
    if attempts_today >= (13 if music_allowed else 10 if six_allowed else 4 if extra_allowed else 2):
        raise RuntimeError('Birthday experiment cap reached: two attempts per rolling 24 hours')
    path = folder / (queue.name + '.json')
    receipt = {'status': 'started', 'started_at': now(), 'queue': str(queue),
               'sha256': digest, 'caption': caption, 'requested_trial_params': {'graduation_strategy': 'MANUAL'}}
    if extra_allowed:
        receipt['authorization'] = '2026-09-14 explicit user request: make more variations and upload those too; two named variants only'
    if six_allowed:
        receipt['authorization'] = '2026-09-14 explicit user request: corrected full bowling payoff plus five new variations, including birthday far from home; six named queues only'
    if music_allowed:
        receipt['authorization'] = '2026-09-14 explicit user request: Indian music revision and camera flip variant, plus a named correction of the one frame seam defect; three named queues only'
    with path.open('x') as handle:
        json.dump(receipt, handle, indent=2)
    path.chmod(0o600)
    command = [str(ROOT / 'bin/instagram-api-publish.sh'), str(queue), '--trial', 'manual']
    env = os.environ.copy()
    for key in ['IG_ACCESS_TOKEN', 'IG_KEYCHAIN_SERVICE', 'IG_USER_ID', 'IG_GRAPH_HOST', 'IG_API_VERSION', 'IG_VIDEO_URL']:
        env.pop(key, None)
    result = subprocess.run(command, capture_output=True, text=True, env=env)
    receipt['publisher_exit_code'] = result.returncode
    receipt['publisher_output'] = result.stdout + result.stderr
    if result.returncode:
        receipt['status'] = 'uncertain_or_failed_do_not_retry'
        save(path, receipt)
        raise RuntimeError('Publisher did not confirm completion; inspect private receipt before retrying')
    try:
        payload = json.loads(result.stdout.split('Published Instagram media', 1)[1].strip())
        receipt['media_id'] = payload['id']
    except (IndexError, KeyError, ValueError):
        receipt['status'] = 'uncertain_do_not_retry'
        save(path, receipt)
        raise RuntimeError('Unrecognized publisher response; inspect private receipt before retrying') from None
    receipt['status'] = 'published'
    receipt['published_at'] = now()
    save(path, receipt)
    try:
        receipt['media'] = api(receipt['media_id'], fields='id,permalink,timestamp,caption')
        receipt['trial_verification_note'] = 'MANUAL trial parameters sent and accepted. This API does not expose a trial status readback field; verify the owner UI separately.'
    except RuntimeError as error:
        receipt['verification_error'] = str(error)
    save(path, receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k != 'publisher_output'}, indent=2))


def reconcile_pre_ingest(queue):
    queue = Path(queue).resolve()
    queue.relative_to(ROOT / 'publishing/queue')
    path = STATE / 'attempts' / (queue.name + '.json')
    receipt = json.loads(path.read_text())
    output = receipt.get('publisher_output', '')
    expected = 'Temporary HTTPS tunnel did not become ready'
    if receipt.get('media_id') or expected not in output or 'Processing status:' in output or 'Published Instagram media' in output:
        raise RuntimeError('Not a proven pre-ingest failure; manual reconciliation is required')
    if any(p.get('caption', '').strip() == receipt['caption'] for p in recent()):
        raise RuntimeError('Caption exists on Instagram; do not retry')
    receipt['status'] = 'confirmed_failed_before_meta_ingest'
    receipt['reconciled_at'] = now()
    receipt['reconciliation'] = 'Publisher exited at HTTPS readiness gate before any Meta mutation; recent captions checked and absent.'
    save(path, receipt)
    archived = STATE / 'pre-ingest-failures' / (queue.name + '-' + dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.json')
    archived.parent.mkdir(parents=True, exist_ok=True)
    path.rename(archived)
    print('Confirmed pre-ingest failure archived. No Meta upload or publication took place. Retry is safe.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['snapshot', 'publish', 'reconcile-pre-ingest'])
    parser.add_argument('queue', nargs='?')
    parser.add_argument('--authorized-extra-batch', action='store_true')
    parser.add_argument('--authorized-birthday-six', action='store_true')
    parser.add_argument('--authorized-music-refresh', action='store_true')
    args = parser.parse_args()
    if args.action != 'snapshot' and not args.queue:
        parser.error('this action needs a queue directory')
    if args.action == 'snapshot':
        snapshot()
    elif args.action == 'publish':
        publish(args.queue, args.authorized_extra_batch, args.authorized_birthday_six, args.authorized_music_refresh)
    else:
        reconcile_pre_ingest(args.queue)
