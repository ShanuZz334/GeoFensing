import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:geolocator/geolocator.dart';
import '../../verification/providers/verification_provider.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/custom_loader.dart';

class DemoSetupDialog extends StatefulWidget {
  const DemoSetupDialog({super.key});

  @override
  State<DemoSetupDialog> createState() => _DemoSetupDialogState();
}

class _DemoSetupDialogState extends State<DemoSetupDialog> {
  late bool _demoEnabled;
  late bool _bypassLimits;
  late TextEditingController _latController;
  late TextEditingController _lngController;
  late TextEditingController _radiusController;
  bool _isLoadingLocation = false;

  @override
  void initState() {
    super.initState();
    final provider = context.read<VerificationProvider>();
    _demoEnabled = provider.demoMode;
    _bypassLimits = provider.bypassLimits;
    _latController = TextEditingController(text: provider.demoLat?.toString() ?? '');
    _lngController = TextEditingController(text: provider.demoLng?.toString() ?? '');
    _radiusController = TextEditingController(text: provider.demoRadius?.toString() ?? '200');

    if (_latController.text.isEmpty && _lngController.text.isEmpty) {
      _fetchCurrentLocation();
    }
  }

  Future<void> _fetchCurrentLocation() async {
    setState(() => _isLoadingLocation = true);
    try {
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.whileInUse || permission == LocationPermission.always) {
        final position = await Geolocator.getCurrentPosition(
          locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
        );
        setState(() {
          _latController.text = position.latitude.toString();
          _lngController.text = position.longitude.toString();
        });
      } else {
        // Permission denied fallback
        _setCampusDefaults();
      }
    } catch (_) {
      _setCampusDefaults();
    } finally {
      if (mounted) setState(() => _isLoadingLocation = false);
    }
  }

  void _setCampusDefaults() {
    if (!mounted) return;
    setState(() {
      _latController.text = '31.2488';
      _lngController.text = '75.6994';
    });
  }

  @override
  void dispose() {
    _latController.dispose();
    _lngController.dispose();
    _radiusController.dispose();
    super.dispose();
  }

  void _save() {
    final lat = double.tryParse(_latController.text);
    final lng = double.tryParse(_lngController.text);
    final rad = double.tryParse(_radiusController.text);

    if (_demoEnabled && (lat == null || lng == null)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter valid coordinates for demo mode')),
      );
      return;
    }

    context.read<VerificationProvider>().setDemoMode(
      enabled: _demoEnabled,
      bypassLimits: _bypassLimits,
      lat: lat,
      lng: lng,
      radius: rad,
    );

    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: AppTheme.surface,
      title: const Row(
        children: [
          Icon(Icons.bug_report_outlined, color: AppTheme.primary),
          SizedBox(width: 10),
          Text('Demo Mode Setup', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
        ],
      ),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Override campus geofence for testing at various locations.',
              style: TextStyle(fontSize: 13, color: Colors.grey),
            ),
            const SizedBox(height: 16),
            SwitchListTile(
              title: const Text('Enable Demo Mode', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold)),
              value: _demoEnabled,
              activeThumbColor: AppTheme.primary,
              contentPadding: EdgeInsets.zero,
              onChanged: (v) => setState(() => _demoEnabled = v),
            ),
            SwitchListTile(
              title: const Text('Disable All Limits', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold)),
              subtitle: const Text('Bypass attempt limits and stop saving data', style: TextStyle(color: Colors.grey, fontSize: 11)),
              value: _bypassLimits,
              activeThumbColor: AppTheme.primary,
              contentPadding: EdgeInsets.zero,
              onChanged: (v) => setState(() => _bypassLimits = v),
            ),
            if (_demoEnabled) ...[
              const SizedBox(height: 4),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton.icon(
                  onPressed: _isLoadingLocation ? null : _fetchCurrentLocation,
                  icon: _isLoadingLocation 
                    ? const SizedBox(height: 14, child: CustomLoader(color: AppTheme.primary)) 
                    : const Icon(Icons.my_location_rounded, size: 16),
                  label: Text(_isLoadingLocation ? 'Locating...' : 'Use Current Location', style: const TextStyle(fontSize: 12)),
                ),
              ),
            ],
            const Divider(),
            const SizedBox(height: 8),
            TextField(
              controller: _latController,
              style: const TextStyle(color: Colors.white),
              decoration: const InputDecoration(
                labelText: 'Target Latitude',
                labelStyle: TextStyle(color: AppTheme.textMedium),
                hintText: 'e.g. 31.2488',
                hintStyle: TextStyle(color: Colors.grey),
                prefixIcon: Icon(Icons.location_on_outlined, color: AppTheme.textMedium),
                enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.grey)),
                focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: AppTheme.primary)),
              ),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              enabled: _demoEnabled,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _lngController,
              style: const TextStyle(color: Colors.white),
              decoration: const InputDecoration(
                labelText: 'Target Longitude',
                labelStyle: TextStyle(color: AppTheme.textMedium),
                hintText: 'e.g. 75.6994',
                hintStyle: TextStyle(color: Colors.grey),
                prefixIcon: Icon(Icons.location_on_outlined, color: AppTheme.textMedium),
                enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.grey)),
                focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: AppTheme.primary)),
              ),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              enabled: _demoEnabled,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _radiusController,
              style: const TextStyle(color: Colors.white),
              decoration: const InputDecoration(
                labelText: 'Radius (Meters)',
                labelStyle: TextStyle(color: AppTheme.textMedium),
                hintText: 'e.g. 200',
                hintStyle: TextStyle(color: Colors.grey),
                prefixIcon: Icon(Icons.circle_outlined, color: AppTheme.textMedium),
                enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.grey)),
                focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: AppTheme.primary)),
              ),
              keyboardType: TextInputType.number,
              enabled: _demoEnabled,
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel', style: TextStyle(color: Colors.grey)),
        ),
        ElevatedButton(
          onPressed: _save,
          style: ElevatedButton.styleFrom(
            backgroundColor: AppTheme.primary,
            foregroundColor: Colors.white,
          ),
          child: const Text('Save Settings'),
        ),
      ],
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
    );
  }
}
