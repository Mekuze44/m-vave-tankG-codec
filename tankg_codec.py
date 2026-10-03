"""M-VAVE TANK-G .tkg preset encoder/decoder.

The file format implemented here is the 21-byte format reverse-engineered by the
user. This module deliberately keeps MOD/Delay/Reverb FX knobs as raw continuous
values instead of converting them to a local 0..40 value per effect zone.

No bank/slot information is stored in .tkg.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


TKG_SIZE = 21

# Raw effect knobs are byte values. The editor displays these as raw + 1.
EFFECT_RAW_MIN = 0
EFFECT_RAW_MAX = 127

MOD_EFFECTS = ("chorus", "phaser", "tremolo")
DELAY_EFFECTS = ("analog", "tape", "dual")
REVERB_EFFECTS = ("room", "spring", "cloud")


def _byte(name: str, value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an integer")
    if not 0 <= value <= 255:
        raise ValueError(f"{name} must be between 0 and 255, got {value}")
    return value


def _range(name: str, value: int, lo: int, hi: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an integer")
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be between {lo} and {hi}, got {value}")
    return value


def _enable(name: str, value: bool | int) -> int:
    if isinstance(value, bool):
        return int(value)
    return _range(name, value, 0, 1)


def encode_effect_display(value: int) -> int:
    """Convert the editor's displayed FX/Mix/Decay value to the raw file byte.

    The editor displays raw + 1, so displayed 1 becomes raw 0.
    Displayed range supported here is 1..128.
    """
    return _range("effect display value", value, 1, 128) - 1


def decode_effect_display(raw: int) -> int:
    """Convert a raw FX/Mix/Decay byte to the value displayed by the editor."""
    return _range("effect raw value", raw, EFFECT_RAW_MIN, EFFECT_RAW_MAX) + 1


def classify_effect_zone(raw: int) -> Literal["effect1", "off", "effect2", "effect3"]:
    """Best-effort classification of a continuous effect knob.

    The physical transition points are approximate. We therefore keep raw values
    authoritative and expose this only as a convenience classifier.

    Chosen practical bands:
      0..39   = effect 1
      40..44  = OFF transition
      45..79  = effect 2
      80..84  = OFF transition
      85..127 = effect 3
    """
    raw = _range("effect raw value", raw, 0, 127)
    if raw <= 39:
        return "effect1"
    if raw <= 44:
        return "off"
    if raw <= 79:
        return "effect2"
    if raw <= 84:
        return "off"
    return "effect3"


@dataclass(slots=True)
class TKGPreset:
    """Human-readable representation of a 21-byte TANK-G preset."""

    amp_enabled: bool = False
    mod_enabled: bool = False
    delay_enabled: bool = False
    reverb_enabled: bool = False

    noise_gate: int = 0
    amp_type: int = 1
    gain: int = 0
    treble: int = 0
    middle: int = 0
    bass: int = 0
    volume: int = 0

    # These three are intentionally RAW values. The software displays raw + 1.
    mod_fx_raw: int = 0
    mod_speed: int = 0
    delay_mix_raw: int = 0
    delay_time: int = 0
    reverb_decay_raw: int = 0
    reverb_mix: int = 0

    # 0 = off, 1..8 = IR slots.
    ir_cab: int = 0

    footswitch_r: int = 0
    footswitch_g: int = 0
    footswitch_b: int = 0

    def validate(self) -> None:
        _enable("amp_enabled", self.amp_enabled)
        _enable("mod_enabled", self.mod_enabled)
        _enable("delay_enabled", self.delay_enabled)
        _enable("reverb_enabled", self.reverb_enabled)

        _range("noise_gate", self.noise_gate, 0, 100)
        _range("amp_type", self.amp_type, 1, 9)

        _range("gain", self.gain, 0, 100)
        _range("treble", self.treble, 0, 100)
        _range("middle", self.middle, 0, 100)

        # Reverse-engineered files can contain values >100 here; byte is safest.
        _byte("bass", self.bass)
        _byte("volume", self.volume)

        _range("mod_fx_raw", self.mod_fx_raw, 0, 127)
        _range("mod_speed", self.mod_speed, 0, 100)
        _range("delay_mix_raw", self.delay_mix_raw, 0, 127)
        _range("delay_time", self.delay_time, 0, 127)
        _range("reverb_decay_raw", self.reverb_decay_raw, 0, 127)
        _range("reverb_mix", self.reverb_mix, 0, 100)

        _range("ir_cab", self.ir_cab, 0, 8)
        _byte("footswitch_r", self.footswitch_r)
        _byte("footswitch_g", self.footswitch_g)
        _byte("footswitch_b", self.footswitch_b)

    @property
    def mod_fx_display(self) -> int:
        return decode_effect_display(self.mod_fx_raw)

    @mod_fx_display.setter
    def mod_fx_display(self, value: int) -> None:
        self.mod_fx_raw = encode_effect_display(value)

    @property
    def delay_mix_display(self) -> int:
        return decode_effect_display(self.delay_mix_raw)

    @delay_mix_display.setter
    def delay_mix_display(self, value: int) -> None:
        self.delay_mix_raw = encode_effect_display(value)

    @property
    def reverb_decay_display(self) -> int:
        return decode_effect_display(self.reverb_decay_raw)

    @reverb_decay_display.setter
    def reverb_decay_display(self, value: int) -> None:
        self.reverb_decay_raw = encode_effect_display(value)

    @property
    def footswitch_rgb(self) -> tuple[int, int, int]:
        return self.footswitch_r, self.footswitch_g, self.footswitch_b

    @footswitch_rgb.setter
    def footswitch_rgb(self, rgb: tuple[int, int, int]) -> None:
        if len(rgb) != 3:
            raise ValueError("footswitch_rgb must contain exactly R, G and B")
        self.footswitch_r, self.footswitch_g, self.footswitch_b = (
            _byte("R", rgb[0]), _byte("G", rgb[1]), _byte("B", rgb[2])
        )

    @property
    def mod_zone(self) -> str:
        return classify_effect_zone(self.mod_fx_raw)

    @property
    def delay_zone(self) -> str:
        return classify_effect_zone(self.delay_mix_raw)

    @property
    def reverb_zone(self) -> str:
        return classify_effect_zone(self.reverb_decay_raw)

    def to_bytes(self) -> bytes:
        """Encode this preset to exactly 21 bytes."""
        self.validate()
        data = bytes((
            _enable("amp_enabled", self.amp_enabled),
            _enable("mod_enabled", self.mod_enabled),
            _enable("delay_enabled", self.delay_enabled),
            _enable("reverb_enabled", self.reverb_enabled),
            self.noise_gate,
            self.amp_type - 1,
            self.gain,
            self.treble,
            self.middle,
            self.bass,
            self.volume,
            self.mod_fx_raw,
            self.mod_speed,
            self.delay_mix_raw,
            self.delay_time,
            self.reverb_decay_raw,
            self.reverb_mix,
            self.ir_cab,
            self.footswitch_r,
            self.footswitch_g,
            self.footswitch_b,
        ))
        assert len(data) == TKG_SIZE
        return data

    @classmethod
    def from_bytes(cls, data: bytes | bytearray | memoryview) -> "TKGPreset":
        """Decode exactly one 21-byte TANK-G preset."""
        raw = bytes(data)
        if len(raw) != TKG_SIZE:
            raise ValueError(f"A TANK-G .tkg preset must be exactly 21 bytes, got {len(raw)}")
        return cls(
            amp_enabled=bool(raw[0]),
            mod_enabled=bool(raw[1]),
            delay_enabled=bool(raw[2]),
            reverb_enabled=bool(raw[3]),
            noise_gate=raw[4],
            amp_type=raw[5] + 1,
            gain=raw[6],
            treble=raw[7],
            middle=raw[8],
            bass=raw[9],
            volume=raw[10],
            mod_fx_raw=raw[11],
            mod_speed=raw[12],
            delay_mix_raw=raw[13],
            delay_time=raw[14],
            reverb_decay_raw=raw[15],
            reverb_mix=raw[16],
            ir_cab=raw[17],
            footswitch_r=raw[18],
            footswitch_g=raw[19],
            footswitch_b=raw[20],
        )

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.write_bytes(self.to_bytes())
        return path

    @classmethod
    def load(cls, path: str | Path) -> "TKGPreset":
        return cls.from_bytes(Path(path).read_bytes())

    def as_dict(self) -> dict[str, object]:
        return {
            "amp_enabled": self.amp_enabled,
            "mod_enabled": self.mod_enabled,
            "delay_enabled": self.delay_enabled,
            "reverb_enabled": self.reverb_enabled,
            "noise_gate": self.noise_gate,
            "amp_type": self.amp_type,
            "gain": self.gain,
            "treble": self.treble,
            "middle": self.middle,
            "bass": self.bass,
            "volume": self.volume,
            "mod_fx_raw": self.mod_fx_raw,
            "mod_fx_display": self.mod_fx_display,
            "mod_speed": self.mod_speed,
            "delay_mix_raw": self.delay_mix_raw,
            "delay_mix_display": self.delay_mix_display,
            "delay_time": self.delay_time,
            "reverb_decay_raw": self.reverb_decay_raw,
            "reverb_decay_display": self.reverb_decay_display,
            "reverb_mix": self.reverb_mix,
            "ir_cab": self.ir_cab,
            "footswitch_rgb": self.footswitch_rgb,
        }


def encode_preset(**kwargs) -> bytes:
    """Convenience function returning a ready-to-write 21-byte preset."""
    return TKGPreset(**kwargs).to_bytes()


def decode_preset(data: bytes) -> TKGPreset:
    return TKGPreset.from_bytes(data)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TANK-G .tkg encoder/decoder")
    sub = parser.add_subparsers(dest="command", required=True)

    dec = sub.add_parser("decode", help="decode a .tkg file")
    dec.add_argument("file")

    enc = sub.add_parser("encode", help="encode a preset from key=value pairs")
    enc.add_argument("output")
    enc.add_argument("pairs", nargs="*", help="field=value")

    args = parser.parse_args()

    if args.command == "decode":
        p = TKGPreset.load(args.file)
        for k, v in p.as_dict().items():
            print(f"{k}={v}")
    else:
        values: dict[str, object] = {}
        bool_fields = {"amp_enabled", "mod_enabled", "delay_enabled", "reverb_enabled"}
        for item in args.pairs:
            if "=" not in item:
                raise SystemExit(f"Invalid pair: {item!r}")
            key, value = item.split("=", 1)
            if key in bool_fields:
                values[key] = value.lower() in {"1", "true", "on", "yes"}
            else:
                values[key] = int(value, 0)
        TKGPreset(**values).save(args.output)
        print(f"Wrote {args.output}")
