# Turkey EPG (Electronic Program Guide)

IPTV-compatible EPG system for Turkish TV channels with automatic updates.

## Features

- ✅ **IPTV Compatible**: Generates channel IDs in multiple formats to work with any IPTV player
- ✅ **Quality Suffix Support**: Supports channel IDs with 4K, HD, FHD, UHD, SD suffixes
- ✅ **Automatic Updates**: GitHub Actions workflow updates EPG every 6 hours
- ✅ **Official Logos**: Uses D-Smart's official CDN for channel logos
- ✅ **Turkey Timezone**: All times displayed in Turkey time (+0300)
- ✅ **150+ Channels**: Covers major Turkish TV channels from D-Smart and beIN Sports
- ✅ **3-Day EPG**: Provides program data for today + 2 days

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

The EPG generates multiple ID formats for each channel to ensure compatibility:

### Example for "Show TV":
- `Show TV` (with space)
- `Show TV 4K`, `Show TV HD`, `Show TV FHD`, `Show TV UHD` (with quality suffixes)
- `ShowTV`, `ShowTV4K`, `ShowTVHD` (CamelCase)
- `ShowTV.tr`, `showtv.tr` (with .tr domain)
- `showtv.dsmart.tr` (D-Smart format)

### Example for "Kanal D":
- `Kanal D` (with space)
- `Kanal D 4K`, `Kanal D HD` (with quality suffixes)
- `KanalD`, `KanalD4K`, `KanalDHD` (CamelCase)
- `KanalD.tr`, `kanald.tr` (with .tr domain)
- `kanald.dsmart.tr` (D-Smart format)

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
- `DAYS_TO_FETCH`: Number of days to fetch (default: 3)
- `TZ_TURKEY`: Timezone offset (default: +0300)
- `REQUEST_TIMEOUT`: API timeout in seconds (default: 30)

## Automatic Updates

The EPG is automatically updated every 6 hours via GitHub Actions:
- Workflow file: `.github/workflows/update-epg.yml`
- Schedule: `0 */6 * * *` (00:00, 06:00, 12:00, 18:00 UTC)
- Manual trigger: Available via GitHub Actions UI

## Data Sources

- **D-Smart**: https://www.dsmart.com.tr/api/v1/public/epg/schedules
- **beIN Sports**: https://beinsports.com.tr/yayin-akisi

## License

MIT License

## Credits

- Inspired by [iptv-org/epg](https://github.com/iptv-org/epg)
- Logo URLs from D-Smart official CDN

## Troubleshooting

### "No Info" in IPTV Player
Make sure your IPTV playlist channel IDs match the EPG channel IDs. Common formats:
- `Show TV 4K`, `Kanal D 4K`, `TRT 1 HD`
- The EPG supports multiple formats automatically

### Logos Not Showing
The EPG uses D-Smart's official CDN. If logos don't appear, check:
1. Your IPTV player supports icon URLs in EPG
2. The channel name exactly matches (case-insensitive)

### Old Program Data
- EPG updates every 6 hours automatically
- Force refresh in your IPTV player settings
- Clear EPG cache in player settings

## Contributing

Pull requests are welcome! For major changes, please open an issue first.

## Support

If you find this useful, please ⭐ star the repository!
