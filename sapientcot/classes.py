#!/usr/bin/env python3
# Copyright Sensors & Signals LLC https://www.snstac.com
# SPDX-License-Identifier: Apache-2.0
"""SAPIENTCOT Class Definitions."""

import asyncio

import pytak
import sapientcot


def _load_message_class(version: str):
    """Return the SapientMessage protobuf class for the configured version."""
    if str(version).lower() in ("v1", "1", "bsi_flex_335_v1_0"):
        from sapient_msg.bsi_flex_335_v1_0 import sapient_message_pb2 as sm
    else:
        from sapient_msg.bsi_flex_335_v2_0 import sapient_message_pb2 as sm
    return sm.SapientMessage


class SapientWorker(pytak.QueueWorker):
    """Read length-delimited SAPIENT protobuf from a Fusion/HLDMM node and emit CoT."""

    async def handle_data(self, message) -> None:
        """Convert a parsed SapientMessage to CoT and enqueue it."""
        event = sapientcot.sapient_to_cot(message, self.config)
        if event:
            await self.put_queue(event)

    async def _read_exactly(self, reader: asyncio.StreamReader, n: int) -> bytes:
        """Read exactly n bytes; raise IncompleteReadError on EOF (worker restarts)."""
        return await reader.readexactly(n)

    async def run(self, number_of_iterations=-1):
        """Connect to the SAPIENT node and stream detections into CoT."""
        self._logger.info("Running %s", self.__class__)

        host: str = self.config.get("SAPIENT_HOST", sapientcot.DEFAULT_SAPIENT_HOST)
        port = int(self.config.get("SAPIENT_PORT", sapientcot.DEFAULT_SAPIENT_PORT))
        version: str = self.config.get("SAPIENT_VERSION", "v2")
        len_bytes = int(self.config.get("SAPIENT_LEN_BYTES", sapientcot.DEFAULT_LEN_BYTES))
        endian: str = self.config.get("SAPIENT_LEN_ENDIAN", sapientcot.DEFAULT_LEN_ENDIAN)

        message_cls = _load_message_class(version)
        self._logger.info("Connecting to SAPIENT node %s:%s (%s)", host, port, version)
        reader, _ = await asyncio.open_connection(host, port)

        while True:
            try:
                header = await self._read_exactly(reader, len_bytes)
            except asyncio.IncompleteReadError:
                self._logger.warning("SAPIENT connection closed; worker will restart.")
                break
            length = int.from_bytes(header, endian)
            if length <= 0 or length > 10_000_000:
                self._logger.warning("Bogus SAPIENT frame length %s; resyncing.", length)
                continue
            payload = await self._read_exactly(reader, length)
            message = message_cls()
            try:
                message.ParseFromString(payload)
            except Exception as exc:  # noqa: BLE001 - protobuf raises DecodeError subclasses
                self._logger.warning("Undecodable SAPIENT frame (%s bytes): %s", length, exc)
                continue
            await self.handle_data(message)
