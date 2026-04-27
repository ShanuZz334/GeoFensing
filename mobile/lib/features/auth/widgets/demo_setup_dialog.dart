import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:geolocator/geolocator.dart';
import '../../verification/providers/verification_provider.dart';
import '../../../core/theme/app_theme.dart';

class DemoSetupDialog extends StatefulWidget {
  const DemoSetupDialog({super.key});

  @override
  State<DemoSetupDialog> createState() => _DemoSetupDialogState();
}

class _DemoSetupDialogState extends State<DemoSetupDialog> {
  late bool _demoEnabled;
  late TextEditingController _latController;
  late TextEditingController _lngController;
  late TextEditingController _radiusController;
  bool _isLoadingLocation = false;

  @override
  void initState() {
    super.initState();
    final provider = context.read<VerificationProvider>();
    _demoEnabled = provider.demoMode;
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
        _setLPUDefaults();
      }
    } catch (_) {
      _setLPUDefaults();
    } finally {
      if (mounted) setState(() => _isLoadingLocation = false);
    }
  }

  void _setLPUDefaults() {
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
      lat: lat,
      lng: lng,
      radius: rad,
    );

    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Row(
        children: [
          Icon(Icons.bug_report_outlined, color: AppTheme.primary),
          SizedBox(width: 10),
          Text('Demo Mode Setup'),
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
              title: const Text('Enable Demo Mode', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
              value: _demoEnabled,
              activeThumbColor: AppTheme.primary,
              contentPadding: EdgeInsets.zero,
              onChanged: (v) => setState(() => _demoEnabled = v),
            ),
            if (_demoEnabled) ...[
              const SizedBox(height: 4),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton.icon(
                  onPressed: _isLoadingLocation ? null : _fetchCurrentLocation,
                  icon: _isLoadingLocation 
                    ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primary)) 
                    : const Icon(Icons.my_location_rounded, size: 16),
                  label: Text(_isLoadingLocation ? 'Locating...' : 'Use Current Location', style: const TextStyle(fontSize: 12)),
                ),
              ),
            ],
            const Divider(),
            const SizedBox(height: 8),
            TextField(
              controller: _latController,
              decoration: const InputDecoration(
                labelText: 'Target Latitude',
                hintText: 'e.g. 31.2488',
                prefixIcon: Icon(Icons.location_on_outlined),
              ),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              enabled: _demoEnabled,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _lngController,
              decoration: const InputDecoration(
                labelText: 'Target Longitude',
                hintText: 'e.g. 75.6994',
                prefixIcon: Icon(Icons.location_on_outlined),
              ),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              enabled: _demoEnabled,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _radiusController,
              decoration: const InputDecoration(
                labelText: 'Radius (Meters)',
                hintText: 'e.g. 200',
                prefixIcon: Icon(Icons.circle_outlined),
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
