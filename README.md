# Turkey EPG (Electronic Program Guide)

IPTV-compatible EPG system for Turkish TV channels with automatic updates.

## Features

- ✅ **IPTV Compatible**: Simple, clean channel IDs for maximum compatibility
- ✅ **UTC Timezone**: All times in UTC (+0000) for universal compatibility
- ✅ **Automatic Updates**: GitHub Actions workflow updates EPG every 6 hours
- ✅ **Official Sources**: Uses TV Plus and beIN Sports official APIs
- ✅ **150+ Channels**: Covers major Turkish TV channels from TV Plus and beIN Sports
- ✅ **Today's EPG**: Provides program data for current day

## Supported Channels

### General/Entertainment
- Kanal D, Show TV, Star TV, ATV, TRT 1, Kanal 7, TV8, NOW (FOX), teve2
- Beyaz TV, ShowMax, TV8.5

### News
- CNN Türk, NTV, TRT Haber, Habertürk, A Haber, Haber Global
- Bloomberg HT, TGRT Haber, TV100, 360

### Sports
- beIN Sports 1-4, beIN Sports Haber
- TRT Spor, A Spor, Eurosport, NBA TV, Spor Smart

### Kids
- Cartoon Network, TRT Çocuk, Minika GO, Minika Çocuk
- Disney Channel, Disney Junior

### Documentary
- National Geographic, Discovery, BBC Earth, TRT Belgesel

### Movies/Series
- FX, Sinema TV, MovieSmart, DiziSmart

## EPG URL

```
https://raw.githubusercontent.com/Dodoizm35/epg-turkish/main/epg/index.xml
```

Or use GitHub Pages:
```
https://dodoizm35.github.io/epg-turkish/epg/index.xml
```

## Channel ID Formats

The EPG uses simple, clean channel IDs for maximum compatibility:

### Examples:
- `atv` - ATV
- `show-tv` - Show TV
- `kanal-d` - Kanal D
- `trt1` - TRT 1
- `fox` - NOW (former FOX)
- `beinsports1.tr` - beIN Sports 1
- `beinsports2.tr` - beIN Sports 2

Each channel has **one single ID** - no aliases, no quality suffixes.

## IPTV Player Setup

### TiviMate
1. Settings → EPG → EPG Source
2. Add URL: `https://raw.githubusercontent.com/Dodoizm35/epg-turkish/main/epg/index.xml`
3. Update interval: 12 hours

### Perfect Player
1. Settings → General → EPG source
2. Add URL: `https://raw.githubusercontent.com/Dodoizm35/epg-turkish/main/epg/index.xml`

### Kodi (PVR IPTV Simple Client)
1. Settings → EPG → XMLTV Location
2. Add URL: `https://raw.githubusercontent.com/Dodoizm35/epg-turkish/main/epg/index.xml`

## Development

### Requirements
- Python 3.8+
- `requests` library

### Installation
```bash
pip install -r requirements.txt
```

### Manual EPG Generation
```bash
python main.py
```

Output will be written to `epg/index.xml`

### Configuration

Edit `config.py` to customize:
- `DAYS_TO_FETCH`: Number of days to fetch (default: 1)
- `TZ_UTC`: Timezone offset (always +0000 for UTC)
- `REQUEST_TIMEOUT`: API timeout in seconds (default: 30)

## Automatic Updates

The EPG is automatically updated every 6 hours via GitHub Actions:
- Workflow file: `.github/workflows/update-epg.yml`
- Schedule: `0 */6 * * *` (00:00, 06:00, 12:00, 18:00 UTC)
- Manual trigger: Available via GitHub Actions UI

## Data Sources

- **TV Plus**: https://tvplus.com.tr/canli-tv/yayin-akisi (Primary source)
- **beIN Sports**: https://beinsports.com.tr/yayin-akisi (Sports channels)

## License

MIT License

## Credits

- Inspired by [iptv-org/epg](https://github.com/iptv-org/epg)
- Logo URLs from D-Smart official CDN

## Troubleshooting

### "No Info" in IPTV Player
Make sure your IPTV playlist channel IDs match the EPG channel IDs. Use simple formats:
- `atv`, `show-tv`, `kanal-d`, `trt1`
- For beIN Sports: `beinsports1.tr`, `beinsports2.tr`

### Logos Not Showing
The EPG includes logo URLs from TV Plus. If logos don't appear, check:
1. Your IPTV player supports icon URLs in EPG
2. The channel name matches the EPG channel ID

### Old Program Data
- EPG updates every 6 hours automatically
- Force refresh in your IPTV player settings
- Clear EPG cache in player settings

## Contributing

Pull requests are welcome! For major changes, please open an issue first.

## Support

If you find this useful, please ⭐ star the repository!
