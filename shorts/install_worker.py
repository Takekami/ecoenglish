"""Install/remove the per-user Mac launch agent (no secrets embedded in plist)."""
import argparse
import os
from pathlib import Path
import plistlib
import subprocess

ROOT=Path(__file__).resolve().parents[1]
LABEL='jp.econenglish.shorts-private-worker'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--remove',action='store_true')
    args=p.parse_args()
    target=Path.home()/'Library/LaunchAgents'/f'{LABEL}.plist'
    domain=f'gui/{os.getuid()}'
    if args.remove:
        subprocess.run(['launchctl','bootout',domain+'/'+LABEL],check=False)
        if target.exists():target.unlink()
        print('Worker removed; credentials, ledger and generated content retained.')
        return
    if target.exists():
        raise SystemExit('Worker already installed; inspect before replacing it.')
    logs=ROOT/'output/shorts-daily';logs.mkdir(parents=True,exist_ok=True)
    data={'Label':LABEL,'ProgramArguments':[str(ROOT/'.venv-youtube/bin/python'),
          str(ROOT/'shorts/daily_worker.py'),'--config',str(ROOT/'.youtube-secrets/worker.json')],
          'WorkingDirectory':str(ROOT),'RunAtLoad':True,'StartInterval':900,
          'ProcessType':'Background','EnvironmentVariables':{'PYTHONUNBUFFERED':'1','PATH':'/usr/bin:/bin:/usr/sbin:/sbin'},
          'StandardOutPath':str(logs/'worker.log'),'StandardErrorPath':str(logs/'worker-error.log')}
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(plistlib.dumps(data));target.chmod(0o600)
    subprocess.run(['launchctl','bootstrap',domain,str(target)],check=True)
    print('Installed:',LABEL,'(every 15 minutes while logged in; RunAtLoad enabled)')


if __name__=='__main__':main()
