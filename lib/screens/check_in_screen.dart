// lib/screens/check_in_screen.dart
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:intl/intl.dart';

class CheckInScreen extends StatefulWidget {
  const CheckInScreen({super.key});

  @override
  State<CheckInScreen> createState() => _CheckInScreenState();
}

class _CheckInScreenState extends State<CheckInScreen> {
  String _currentTime = '';
  String _distance = 'Press to check distance';
  double _currentDistanceInKm = 0;  // Added this line to fix the error
  bool _hasCheckedDistance = false;  // Added to track if distance was checked

  // Example company location (replace with your company's coordinates)
  final double companyLat = 21.0167393;
  final double companyLng = 105.80558;

  @override
  void initState() {
    super.initState();
    _updateTime();
  }

  void _updateTime() {
    if (!mounted) return;
    setState(() {
      _currentTime = DateFormat('HH:mm').format(DateTime.now());
    });
    Future.delayed(const Duration(seconds: 1), _updateTime);
  }

  Future<void> _checkDistance() async {
    try {
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          setState(() {
            _distance = 'Location permission denied';
          });
          return;
        }
      }

      Position position = await Geolocator.getCurrentPosition();
      double distanceInMeters = Geolocator.distanceBetween(
        position.latitude,
        position.longitude,
        companyLat,
        companyLng,
      );

      setState(() {
        _currentDistanceInKm = distanceInMeters / 1000;
        _distance = '${_currentDistanceInKm.toStringAsFixed(2)} km';
        _hasCheckedDistance = true;
      });
    } catch (e) {
      setState(() {
        _distance = 'Error getting location';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Check In/Out'),
        centerTitle: true,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              _currentTime,
              style: const TextStyle(
                fontSize: 64,
              ),
            ),
            const SizedBox(height: 40),
            ElevatedButton(
              onPressed: _checkDistance,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
              ),
              child: const Text(
                'Check Distance to Office',
                style: TextStyle(fontSize: 16),
              ),
            ),
            const SizedBox(height: 20),
            Text(
              _distance,
              style: const TextStyle(fontSize: 32),
            ),
            const SizedBox(height: 40),
            if (_hasCheckedDistance) ...[
              ElevatedButton(
                onPressed: _currentDistanceInKm <= 5 ? () {
                  // TODO: Implement face recognition
                } : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 20),
                  disabledBackgroundColor: Colors.grey,
                  disabledForegroundColor: Colors.white70,
                ),
                child: Text(
                  _currentDistanceInKm <= 5 ? 'CHECK IN NOW' : 'TOO FAR FROM OFFICE',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              if (_currentDistanceInKm > 5) ...[
                const SizedBox(height: 10),
                Text(
                  'Must be within 5km to check in',
                  style: TextStyle(
                    color: Colors.red[400],
                    fontSize: 14,
                  ),
                ),
              ],
            ],
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    // Cancel any pending timers or async operations
    super.dispose();
  }
}