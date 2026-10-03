# M-VAVE TANK-G .tkg Codec

Biblioteca Python para **codificar e decodificar** presets do pedal **M-VAVE TANK-G** no formato binário `.tkg`.

O projeto inclui:
- Documentação completa do formato binário de 21 bytes.
- Encoder/decoder em Python (sem dependências externas).
- CLI para uso rápido no terminal.

---

## 📦 Sobre o Formato `.tkg`

Cada preset do TANK-G é um arquivo binário de **exatamente 21 bytes**. Cada byte representa um parâmetro do pedal, na seguinte ordem:

| Offset | Parâmetro          | Faixa / Valores                          |
|--------|--------------------|------------------------------------------|
| 0      | AMP Enable         | `0` = off, `1` = on                      |
| 1      | MOD Enable         | `0` = off, `1` = on                      |
| 2      | Delay Enable       | `0` = off, `1` = on                      |
| 3      | Reverb Enable      | `0` = off, `1` = on                      |
| 4      | Noise Gate         | `0–100`                                  |
| 5      | Amp Type − 1       | `0–8` → Amp Types `1–9`                  |
| 6      | Gain               | `0–100`                                  |
| 7      | Treble             | `0–100`                                  |
| 8      | Middle             | `0–100`                                  |
| 9      | Bass               | `0–107+` (limite superior em investigação) |
| 10     | Volume             | `0–127`                                  |
| 11     | MOD FX (raw)       | `0–127`                                  |
| 12     | MOD Speed          | `0–100`                                  |
| 13     | Delay Mix (raw)    | `0–127`                                  |
| 14     | Delay Time         | `0–100`                                  |
| 15     | Reverb Decay (raw) | `0–127`                                  |
| 16     | Reverb Mix         | `0–100`                                  |
| 17     | IR CAB             | `0` = off, `1–8` = IR slots              |
| 18     | Footswitch R       | `0–255`                                  |
| 19     | Footswitch G       | `0–255`                                  |
| 20     | Footswitch B       | `0–255`                                  |

> **Nota:** Os limites exatos ainda estão sendo investigados. Contribuições são bem-vindas.

### 🎛️ Efeitos MOD / Delay / Reverb

Cada seção (MOD, Delay, Reverb) possui **3 efeitos selecionáveis** através de um único knob contínuo. O valor armazenado no arquivo é a **posição absoluta do knob**, não um par "tipo + valor".

**MOD:** `Chorus`, `Phaser`, `Tremolo`  
**Delay:** `Analog`, `Tape`, `Dual`  
**Reverb:** `Room`, `Spring`, `Cloud`

Faixas aproximadas de classificação (baseadas em observação):

| Faixa raw | Zona             |
|-----------|------------------|
| `0–39`    | Efeito 1         |
| `40–44`   | Transição / OFF  |
| `45–79`   | Efeito 2         |
| `80–84`   | Transição / OFF  |
| `85–127`  | Efeito 3         |

> **Importante:** Os valores **raw** são autoritativos. A classificação por zona é apenas uma conveniência.

### 🔄 Conversão de Valores (Raw ↔ Display)

Para **MOD FX**, **Delay Mix** e **Reverb Decay**, o editor do pedal exibe o valor como `raw + 1`.

| Valor armazenado (raw) | Valor exibido no editor |
|------------------------|-------------------------|
| `39`                   | `40`                    |
| `127`                  | `128`                   |

O encoder/decoder faz essa conversão automaticamente através das propriedades `*_display`.

---

## 🚀 Instalação

O projeto **não possui dependências externas**. Requer apenas **Python 3.10+**.

```bash
git clone https://github.com/SEU_USUARIO/m-vave-tank-g-codec.git
cd m-vave-tank-g-codec
```

---

🎮 Uso

Via CLI (linha de comando)

Decodificar um preset existente:

```bash
python tankg_codec.py decode meu_preset.tkg
```

Saída:

```
amp_enabled=True
mod_enabled=True
...
gain=50
amp_type=3
...
```

Codificar um novo preset:

```bash
python tankg_codec.py encode novo.tkg \
  amp_enabled=1 mod_enabled=1 delay_enabled=1 reverb_enabled=1 \
  noise_gate=40 amp_type=3 gain=50 treble=60 middle=50 bass=55 volume=80 \
  mod_fx_raw=20 mod_speed=30 delay_mix_raw=60 delay_time=50 \
  reverb_decay_raw=100 reverb_mix=70 ir_cab=1 \
  footswitch_r=0 footswitch_g=100 footswitch_b=255
```

Via Python (biblioteca)

```python
from tankg_codec import TKGPreset

# Carregar um preset existente
preset = TKGPreset.load("meu_preset.tkg")
print(preset.gain, preset.amp_type, preset.footswitch_rgb)

# Criar um novo preset do zero
novo = TKGPreset(
    amp_enabled=True,
    mod_enabled=True,
    delay_enabled=True,
    reverb_enabled=True,
    noise_gate=40,
    amp_type=3,        # Amp Type 3 (armazenado como byte 2)
    gain=50,
    treble=60,
    middle=50,
    bass=55,
    volume=80,
    mod_fx_raw=20,     # Chorus suave
    mod_speed=30,
    delay_mix_raw=60,  # Tape Delay
    delay_time=50,
    reverb_decay_raw=100,  # Cloud Reverb
    reverb_mix=70,
    ir_cab=1,
    footswitch_rgb=(0, 100, 255),
)

novo.save("meu_timbre.tkg")
```

Usando as propriedades de display

```python
preset = TKGPreset()

# Definir o valor como aparece no editor do pedal
preset.mod_fx_display = 40      # raw armazenado = 39
preset.delay_mix_display = 80   # raw armazenado = 79

print(preset.mod_fx_raw)        # 39
print(preset.mod_fx_display)    # 40
```

---

📖 Exemplo de Preset (todos os parâmetros no máximo)

Um preset real com todos os parâmetros no máximo:

```
01 01 01 01 64 08 64 64 64 6B 7F 7F 64 7F 64 7F 64 08 00 00 FF
```

Em decimal:

```
1, 1, 1, 1, 100, 8, 100, 100, 100, 107,
127, 127, 100, 127, 100, 127, 100, 8, 0, 0, 255
```

Isso confirma:

· Noise Gate máximo observado = 100
· Amp Type máximo = 9 (byte 8)
· Gain / Treble / Middle = 100
· Bass pode chegar a pelo menos 107
· Volume = 127
· MOD FX = 127
· MOD Speed = 100
· Delay Mix = 127
· Delay Time = 100
· Reverb Decay = 127
· Reverb Mix = 100
· IR máximo = 8
· RGB = 0, 0, 255 (azul puro)

---

🧪 Estrutura do Projeto

```
m-vave-tank-g-codec/
├── README.md
├── LICENSE
└── tankg_codec.py
```

---

🤝 Contribuindo

Contribuições são muito bem-vindas, especialmente nas seguintes áreas:

· Refinamento dos limites exatos dos parâmetros (especialmente Bass e Volume).
· Mapeamento preciso das zonas de transição dos knobs de MOD / Delay / Reverb.
· Testes com presets reais gravados do pedal.
· Adaptação do código para outros pedais da linha M-VAVE.
· Tradução da documentação para outros idiomas.

Para contribuir:

1. Faça um fork do repositório.
2. Crie uma branch (git checkout -b feature/minha-contribuicao).
3. Commit suas mudanças (git commit -am 'Adiciona X').
4. Faça push (git push origin feature/minha-contribuicao).
5. Abra um Pull Request.

---

🙏 Créditos

Engenharia reversa e implementação original por Mekuze.

Este projeto não possui vínculo oficial com a M-VAVE. É uma iniciativa independente da comunidade, feita para facilitar a criação e o compartilhamento de presets.