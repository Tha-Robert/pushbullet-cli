#!/usr/bin/env python

import click
import os
import os.path
from pushbullet import PushBullet
import sys
from contextlib import contextmanager


KEY_PATH = os.path.expanduser("~/.pushbulletkey")


@contextmanager
def private_files():
    oldmask = os.umask(0o77)
    try:
        yield
    finally:
        os.umask(oldmask)


class NoApiKey(Exception):
    pass


def _get_api_key():
    if 'PUSHBULLET_KEY' in os.environ:
        return os.environ['PUSHBULLET_KEY']

    if not os.path.isfile(KEY_PATH):
        raise NoApiKey()

    with open(KEY_PATH, "r") as api_file:
        return api_file.readline().rstrip()


def _push(data_type, message=None, channel=None, device=None, file_path=None):
    try:
        api_key = _get_api_key()
    except NoApiKey:
        click.echo("No API key was specified. Either run pb set_key to set a permanent key or pass the desired key in PUSHBULLET_KEY environment vaiable.")
        click.echo("You can find your key at <https://www.pushbullet.com/account>.")
        return 1

    pb = PushBullet(api_key)

    data = {}
    if device is not None:
        data["device"] = device

    # upload file if necessary
    if data_type == "file":
        with open(file_path, "rb") as f:
            file_data = pb.upload_file(f, os.path.basename(file_path))

        data.update(file_data)

    if channel is not None:
        pb = channel

    if data_type == "file":
        pb.push_file(**data)
    elif data_type == "url":
        pb.push_link(title=message, url=message, **data)
    elif data_type == "text":
        pb.push_note(title="Note", body=message, **data)
    else:
        raise Exception("Unknown data type")


@click.group()
def main():
    pass


@main.group()
@click.option("-d", "--device", type=str, default=None, help="Push to a specific device instead of all devices.")
@click.option("-c", "--channel", type=str, default=None, help="Push to a channel.")
@click.pass_context
def push(ctx, device, channel):
    if device is not None and channel is not None:
        click.echo("Please specify either device, channel or non of them.")
        ctx.exit()


@push.command()
@click.argument('source', type=click.Path(exists=True))
@click.pass_context
def file(ctx, source):
    kwargs = dict(ctx.parent.params)
    kwargs['file_path'] = click.format_filename(source)
    kwargs['data_type'] = 'file'
    _push(**kwargs)


@push.command()
@click.argument('message', default=None, required=False)
@click.pass_context
def text(ctx, message):
    if message is None:
        print("Enter your message: ")
        message = sys.stdin.read()

    kwargs = dict(ctx.parent.params)
    kwargs['message'] = message
    kwargs['data_type'] = 'text'
    _push(**kwargs)


@push.command()
@click.argument('url')
@click.pass_context
def link(ctx, url):
    kwargs = dict(ctx.parent.params)
    kwargs['message'] = url
    kwargs['data_type'] = 'url'
    _push(**kwargs)
