#!/usr/bin/env python
''' The OUT operation for bender resource'''
from __future__ import print_function

import json

from payload import PayLoad
from base import Base, fail_unless, template_with_regex, read_if_exists, read_content_from_file


class Out(Base):
    ''' Out resource'''

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)
        self.metadata = []
        self.path = kwargs.get("path")
        self.reply_attachments = read_if_exists(self.working_dir, kwargs.get("reply_attachments"))
        self.reply = read_if_exists(self.working_dir, kwargs.get("reply"))
        self.reply_thread = kwargs.get("reply_thread", True)
        # Get context from original message
        context_json_path = '{}/{}/bender.json'.format(self.working_dir, self.path)
        context_content = read_content_from_file(context_json_path)
        context_content = self.serialize_json(context_content)
        # Initialize from original message
        self.version = context_content["version"]
        self.metadata = context_content["metadata"]
        self.original_msg = context_content["original_msg"]

    @staticmethod
    def serialize_json(json_string):
        ''' Serialize a JSON strong into a python object'''
        try:
            serialized = json.loads(json_string)
        except ValueError as value_error:
            fail_unless(False, "JSON Input error: {}".format(value_error))
        return serialized

    def _reply(self, thread_timestamp=False, text=False, attachments=False):
        args = {}
        if thread_timestamp:
            args.update({"thread_ts": thread_timestamp})
        if text:
            args.update({"text": text})
        if attachments:
            args.update({"attachments": attachments})

        self._call_api("chat.postMessage",
                       channel=self.channel_id,
                       parse="full",
                       **args)

    def out_logic(self):
        """Concourse resource `out` logic """

        regex = self._msg_grammar(self.original_msg)
        if self.reply:
            self.reply = template_with_regex(self.reply, regex)

        if self.reply_attachments:
            self.reply_attachments = template_with_regex(self.reply_attachments, regex)
            self.reply_attachments = self.serialize_json(self.reply_attachments)

        if self.reply_thread:
            reply_to_thread = self.version["id_ts"]
        else:
            reply_to_thread = False
        self._reply(thread_timestamp=reply_to_thread,
                    text=self.reply,
                    attachments=self.reply_attachments)

    def out_output(self):
        """Concourse resource `out` output """
        output = {"version": self.version, "metadata": self.metadata}
        print(json.dumps(output, indent=4, sort_keys=True))


def main():
    ''' Main `out` entry point'''
    payload = PayLoad()
    fail_unless(payload.args.get("path"), "path is required, but not defined.")
    if not payload.args.get("reply") and not payload.args.get("reply_attachments"):
        fail_unless(False, "'reply' or 'reply_attachments' paramater required, but not defined.")

    slack_client = Out(**payload.args)
    slack_client.out_logic()
    slack_client.out_output()

if __name__ == '__main__':
    main()
