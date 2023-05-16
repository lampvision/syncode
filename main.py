#!/usr/bin/env python3
# coding: utf-8

import time
import argparse
import subprocess
import logging
import importlib
from pathlib import Path
from datetime import datetime

import libtmux
import hosts
from prettytable import PrettyTable


def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


class Syncode(object):
    def __init__(self, cfg):
        self.cfg = cfg
        self.app_name = cfg.app_name
        self.session_name = cfg.app_name
        self.logger = self._get_logger(self.session_name, Path(cfg.log_path))
        self.job_count = {'runing': 0, 'crashed': 0}
        self.session = self._get_session(self.app_name)
        self.jobs = []

    def run(self):
        while True:
            self._check_run_jobs()
            self._add_new_jobs()
            self._start_new_jobs()
            self._flush_monitor()
            time.sleep(self.cfg.sleep_interval)

    def _check_run_jobs(self):
        for job in self.jobs:
            # @TODO: find a better way to check window's state
            # @TODO: how to address error
            if job['state'] == 'runing':
                try:
                    if len(job['window'].attached_pane) == 0:
                        job.update({
                            'state': 'crashed',
                            'stop_time': datetime.now(),
                        })
                        self.job_count['run'] -= 1
                        self.job_count['crashed'] += 1

                        self.logger.info(f'finish job {job["name"]}')

                except Exception as e:
                    job.update({
                        'state': 'crashed',
                        'stop_time': datetime.now(),
                    })

                    self.job_count['runing'] -= 1
                    self.job_count['crashed'] += 1

                    self.logger.info(f'finish job {job["name"]}')
                    self.logger.error(e)

    def _add_new_jobs(self):
        importlib.reload(hosts)
        from hosts import HOSTS
        for sess_name, host in HOSTS.items():
            cmd = f'''when-changed -v -r -1 -s {host['source_path']}  -c \"rsync -auvz --timeout=5 {host['source_path']}/ {host['host_name']}:{host['dest_path']}; echo \\"\\033[0;31m\\$(date)\\033[0m\\n\\"\" '''
            print(cmd)
            if not self._job_exists(sess_name):
                self.jobs.append({
                    'name': sess_name,
                    'state': 'wait',
                    'cmd': cmd,
                    'window': None,
                    'window_index': None,
                    'start_time': None,
                    'stop_time': None,
                })

                self.logger.info(f'add job {sess_name}')

    def _job_exists(self, sess_name):
        for job in self.jobs:
            if job['name'] == sess_name:
                return True
        return False

    def _start_new_jobs(self):
        for job in self.jobs:
            if job['state'] == 'wait':
                cmd = job["cmd"]
                window = self.session.new_window(attach=False, window_name=job['name'], window_shell=cmd)

                job.update({
                    'window': window,
                    'window_index': window['window_index'],
                    'state': 'runing',
                    'start_time': datetime.now(),
                })

                self.job_count['runing'] += 1

                self.logger.info(f'start job {job["name"]}')

                time.sleep(5)   # avoid start jobs at the same time

    def _flush_monitor(self):
        subprocess.call("clear")

        table = PrettyTable()
        table.field_names = ['Name', 'State', 'Tmux', 'Start', 'Stop', 'Duration (s)']

        cmds = []
        for job in self.jobs:
            start_time = '' if job['start_time'] is None else \
                job['start_time'].strftime("%Y/%m/%d %H:%M:%S")
            stop_time = '' if job['stop_time'] is None else \
                job['stop_time'].strftime("%Y/%m/%d %H:%M:%S")
            duration = '' if job['stop_time'] is None else \
                strfdelta((job['stop_time'] - job['start_time']),
                          '{days} days {hours}:{minutes}:{seconds}')
            table.add_row([job['name'], job['state'], job['window_index'], start_time, stop_time, duration])
            cmds.append(job['cmd'])

        print(table)
        print(f'{datetime.now().strftime("%b %d %Y %H:%M:%S")} ({self.cfg.sleep_interval}s)    '
              f'runing: {self.job_count["runing"]} crashed: {self.job_count["crashed"]}')

        print('\n'.join(cmds))

    def _get_session(self, name):
        server = libtmux.Server()

        session = server.find_where({'session_name': name})
        if session is None:
            session = server.new_session(session_name=name, attach=False)

        return session

    def _get_logger(self, name, save_dpath):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s: %(levelname)5s [%(filename)s:%(lineno)4d] %(message)s",
            "%Y-%m-%d %H:%M:%S")

        log_fpath = save_dpath / f'{name}-{datetime.now().strftime("%Y%m%d%H%M%S")}.log'
        log_fpath.parent.mkdir(parents=True, exist_ok=True)

        fh = logging.FileHandler(log_fpath)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        return logger


def parse_args():
    parser = argparse.ArgumentParser(
        description=None,
        # show default in -h
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-c', '--config', dest='config_path', type=Path,
                        default='./xxx',)
    parser.add_argument('-l', '--log', dest='log_path', type=Path,
                        default='./logs/',)
    parser.add_argument('-n', '--name', dest='app_name', type=str,
                        default='Syncode',)
    parser.add_argument('-i', '--interval', dest='sleep_interval', type=int,
                        default=60)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    syncode = Syncode(args)
    syncode.run()


if __name__ == '__main__':
    main()
