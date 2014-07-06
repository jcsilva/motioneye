
# Copyright (c) 2013 Calin Crisan
# This file is part of motionEye.
#
# motionEye is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>. 

import datetime
import logging
import multiprocessing
import os
import signal
import tornado

import mediafiles
import settings


_process = None


def start():
    if running():
        raise Exception('thumbnailer is already running')

    _run_process()


def stop():
    global _process
    
    if not running():
        raise Exception('thumbnailer is not running')
    
    if _process.is_alive():
        _process.join(timeout=10)
    
    if _process.is_alive():
        logging.error('thumbnailer process did not finish in time, killing it...')
        os.kill(_process.pid, signal.SIGKILL)

    _process = None


def running():
    return _process is not None


def _run_process():
    global _process
    
    if not _process or not _process.is_alive(): # check that the previous process has finished
        logging.debug('running thumbnailer process...')

        _process = multiprocessing.Process(target=_do_next_movie_thumbail)
        _process.start()

    # schedule the next call
    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.add_timeout(datetime.timedelta(seconds=settings.THUMBNAILER_INTERVAL), _run_process)


def _do_next_movie_thumbail():
    # this will be executed in a separate subprocess
    
    # ignore the terminate and interrupt signals in this subprocess
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    
    try:
        mediafiles.make_next_movie_preview()
         
    except Exception as e:
        logging.error('failed to make movie thumbnail: %(msg)s' % {
                'msg': unicode(e)}, exc_info=True)
