#!/usr/bin/python
#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for logger.py and package version requirements."""

import importlib.metadata
import logging
import sys
import unittest
from unittest.mock import MagicMock

from logger import CustomJsonFormatter, getJSONLogger


class TestCustomJsonFormatterAddFields(unittest.TestCase):
    """Tests for CustomJsonFormatter.add_fields."""

    def setUp(self):
        self.formatter = CustomJsonFormatter(
            '%(timestamp)s %(severity)s %(name)s %(message)s'
        )

    def _make_log_record(self, level=logging.INFO, msg='test message'):
        record = logging.LogRecord(
            name='test_logger',
            level=level,
            pathname='test_file.py',
            lineno=1,
            msg=msg,
            args=(),
            exc_info=None,
        )
        return record

    def test_timestamp_added_when_missing(self):
        """add_fields sets timestamp from record.created when not already present."""
        log_record = {}
        record = self._make_log_record()
        self.formatter.add_fields(log_record, record, {})
        self.assertIn('timestamp', log_record)
        self.assertEqual(log_record['timestamp'], record.created)

    def test_timestamp_not_overwritten_when_present(self):
        """add_fields does not overwrite an existing timestamp in log_record."""
        existing_ts = 9999999.0
        log_record = {'timestamp': existing_ts}
        record = self._make_log_record()
        self.formatter.add_fields(log_record, record, {})
        self.assertEqual(log_record['timestamp'], existing_ts)

    def test_severity_uppercased_when_present(self):
        """add_fields uppercases an existing severity value."""
        log_record = {'severity': 'info'}
        record = self._make_log_record(level=logging.INFO)
        self.formatter.add_fields(log_record, record, {})
        self.assertEqual(log_record['severity'], 'INFO')

    def test_severity_uppercased_when_already_upper(self):
        """add_fields leaves severity unchanged when already uppercase."""
        log_record = {'severity': 'WARNING'}
        record = self._make_log_record(level=logging.WARNING)
        self.formatter.add_fields(log_record, record, {})
        self.assertEqual(log_record['severity'], 'WARNING')

    def test_severity_set_from_levelname_when_absent(self):
        """add_fields sets severity from record.levelname when not in log_record."""
        log_record = {}
        record = self._make_log_record(level=logging.ERROR)
        self.formatter.add_fields(log_record, record, {})
        self.assertEqual(log_record['severity'], 'ERROR')

    def test_severity_set_from_levelname_for_debug(self):
        """add_fields sets severity from record.levelname for DEBUG level."""
        log_record = {}
        record = self._make_log_record(level=logging.DEBUG)
        self.formatter.add_fields(log_record, record, {})
        self.assertEqual(log_record['severity'], 'DEBUG')

    def test_severity_set_from_levelname_for_warning(self):
        """add_fields sets severity from record.levelname for WARNING level."""
        log_record = {}
        record = self._make_log_record(level=logging.WARNING)
        self.formatter.add_fields(log_record, record, {})
        self.assertEqual(log_record['severity'], 'WARNING')

    def test_severity_set_from_levelname_for_critical(self):
        """add_fields sets severity from record.levelname for CRITICAL level."""
        log_record = {}
        record = self._make_log_record(level=logging.CRITICAL)
        self.formatter.add_fields(log_record, record, {})
        self.assertEqual(log_record['severity'], 'CRITICAL')

    def test_message_dict_fields_passed_to_super(self):
        """add_fields passes message_dict fields through to log_record via super."""
        log_record = {}
        record = self._make_log_record()
        message_dict = {'extra_field': 'extra_value'}
        self.formatter.add_fields(log_record, record, message_dict)
        # The super call merges message_dict into log_record
        self.assertIn('extra_field', log_record)
        self.assertEqual(log_record['extra_field'], 'extra_value')

    def test_severity_mixed_case_is_uppercased(self):
        """add_fields uppercases a mixed-case severity value."""
        log_record = {'severity': 'Warning'}
        record = self._make_log_record(level=logging.WARNING)
        self.formatter.add_fields(log_record, record, {})
        self.assertEqual(log_record['severity'], 'WARNING')

    def test_timestamp_and_severity_both_set_for_fresh_record(self):
        """add_fields sets both timestamp and severity when neither is present."""
        log_record = {}
        record = self._make_log_record(level=logging.INFO)
        self.formatter.add_fields(log_record, record, {})
        self.assertIn('timestamp', log_record)
        self.assertIn('severity', log_record)
        self.assertEqual(log_record['timestamp'], record.created)
        self.assertEqual(log_record['severity'], 'INFO')


class TestGetJSONLogger(unittest.TestCase):
    """Tests for the getJSONLogger factory function."""

    def tearDown(self):
        # Clean up any loggers created during tests to avoid handler leakage
        for name in ('test.json.logger', 'another.logger', 'propagate.test'):
            logger = logging.getLogger(name)
            logger.handlers.clear()

    def test_returns_logger_with_correct_name(self):
        """getJSONLogger returns a Logger with the specified name."""
        logger = getJSONLogger('test.json.logger')
        self.assertEqual(logger.name, 'test.json.logger')

    def test_logger_level_is_info(self):
        """getJSONLogger sets the logger level to INFO."""
        logger = getJSONLogger('test.json.logger')
        self.assertEqual(logger.level, logging.INFO)

    def test_logger_has_stream_handler(self):
        """getJSONLogger attaches a StreamHandler to the logger."""
        logger = getJSONLogger('test.json.logger')
        stream_handlers = [
            h for h in logger.handlers if isinstance(h, logging.StreamHandler)
        ]
        self.assertGreater(len(stream_handlers), 0)

    def test_handler_outputs_to_stdout(self):
        """getJSONLogger's StreamHandler writes to sys.stdout."""
        logger = getJSONLogger('test.json.logger')
        stream_handlers = [
            h for h in logger.handlers if isinstance(h, logging.StreamHandler)
        ]
        self.assertTrue(
            any(h.stream is sys.stdout for h in stream_handlers)
        )

    def test_handler_uses_custom_json_formatter(self):
        """getJSONLogger's handler uses a CustomJsonFormatter."""
        logger = getJSONLogger('test.json.logger')
        stream_handlers = [
            h for h in logger.handlers if isinstance(h, logging.StreamHandler)
        ]
        self.assertTrue(
            any(isinstance(h.formatter, CustomJsonFormatter) for h in stream_handlers)
        )

    def test_propagate_is_false(self):
        """getJSONLogger sets propagate to False to avoid duplicate log output."""
        logger = getJSONLogger('propagate.test')
        self.assertFalse(logger.propagate)

    def test_different_names_return_different_loggers(self):
        """getJSONLogger returns distinct Logger instances for different names."""
        logger_a = getJSONLogger('test.json.logger')
        logger_b = getJSONLogger('another.logger')
        self.assertNotEqual(logger_a.name, logger_b.name)

    def test_returns_logging_logger_instance(self):
        """getJSONLogger returns an instance of logging.Logger."""
        logger = getJSONLogger('test.json.logger')
        self.assertIsInstance(logger, logging.Logger)


class TestRequirementsPackageVersions(unittest.TestCase):
    """Tests that installed package versions match the versions specified in requirements.in.

    These tests cover only the packages whose versions were changed in this PR.
    """

    def _get_version(self, package_name):
        return importlib.metadata.version(package_name)

    def test_google_api_core_version(self):
        """google-api-core must be 2.30.3 as specified in requirements.in."""
        self.assertEqual(self._get_version('google-api-core'), '2.30.3')

    def test_grpcio_version(self):
        """grpcio must be 1.80.0 as specified in requirements.in."""
        self.assertEqual(self._get_version('grpcio'), '1.80.0')

    def test_grpcio_health_checking_version(self):
        """grpcio-health-checking must be 1.80.0 as specified in requirements.in."""
        self.assertEqual(self._get_version('grpcio-health-checking'), '1.80.0')

    def test_python_json_logger_version(self):
        """python-json-logger must be 4.1.0 as specified in requirements.in."""
        self.assertEqual(self._get_version('python-json-logger'), '4.1.0')

    def test_google_cloud_trace_version(self):
        """google-cloud-trace must be 1.19.0 as specified in requirements.in."""
        self.assertEqual(self._get_version('google-cloud-trace'), '1.19.0')

    def test_requests_version(self):
        """requests must be 2.33.1 as specified in requirements.in."""
        self.assertEqual(self._get_version('requests'), '2.33.1')

    def test_opentelemetry_distro_version(self):
        """opentelemetry-distro must be 0.62b0 as specified in requirements.in."""
        self.assertEqual(self._get_version('opentelemetry-distro'), '0.62b0')

    def test_opentelemetry_instrumentation_grpc_version(self):
        """opentelemetry-instrumentation-grpc must be 0.62b0 as specified in requirements.in."""
        self.assertEqual(self._get_version('opentelemetry-instrumentation-grpc'), '0.62b0')

    def test_opentelemetry_exporter_otlp_proto_grpc_version(self):
        """opentelemetry-exporter-otlp-proto-grpc must be 1.41.0 as specified in requirements.in."""
        self.assertEqual(self._get_version('opentelemetry-exporter-otlp-proto-grpc'), '1.41.0')

    def test_no_old_google_api_core_version(self):
        """google-api-core must NOT be the old version 2.28.1 (regression guard)."""
        self.assertNotEqual(self._get_version('google-api-core'), '2.28.1')

    def test_no_old_grpcio_version(self):
        """grpcio must NOT be the old version 1.76.0 (regression guard)."""
        self.assertNotEqual(self._get_version('grpcio'), '1.76.0')

    def test_no_old_python_json_logger_version(self):
        """python-json-logger must NOT be the old version 4.0.0 (regression guard)."""
        self.assertNotEqual(self._get_version('python-json-logger'), '4.0.0')

    def test_no_old_requests_version(self):
        """requests must NOT be the old version 2.32.5 (regression guard)."""
        self.assertNotEqual(self._get_version('requests'), '2.32.5')

    def test_no_old_opentelemetry_exporter_version(self):
        """opentelemetry-exporter-otlp-proto-grpc must NOT be 1.39.1 (regression guard)."""
        self.assertNotEqual(
            self._get_version('opentelemetry-exporter-otlp-proto-grpc'), '1.39.1'
        )


if __name__ == '__main__':
    unittest.main()