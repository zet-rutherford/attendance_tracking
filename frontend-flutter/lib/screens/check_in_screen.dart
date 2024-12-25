// lib/screens/check_in_screen.dart
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:intl/intl.dart';
import 'package:camera/camera.dart';
import 'dart:io';
import '../services/attendance_service.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'dart:convert';

class CheckInScreen extends StatefulWidget {
  const CheckInScreen({super.key});

  @override
  State<CheckInScreen> createState() => _CheckInScreenState();
}

class _CheckInScreenState extends State<CheckInScreen> {
  String _currentTime = '';
  String _distance = 'Press to check distance';
  int _currentDistanceInMeters = 0;
  bool _hasCheckedDistance = false;
  bool _isCameraActive = false;
  bool _isProcessing = false;
  bool _isLoading = true;
  AttendanceRecord? _todayCheckIn;

  // Camera related variables
  List<CameraDescription>? cameras;
  CameraController? _cameraController;
  File? _capturedImage;

  // Company location (replace with your company's coordinates)
  final double companyLat = 21.0167393;
  final double companyLng = 105.80558;

  @override
  void initState() {
    super.initState();
    _updateTime();
    _initCamera();
    _loadTodayRecord();
  }

  void _updateTime() {
    if (!mounted) return;
    setState(() {
      _currentTime = DateFormat('HH:mm').format(DateTime.now());
    });
    Future.delayed(const Duration(seconds: 1), _updateTime);
  }

  Future<void> _initCamera() async {
    try {
      cameras = await availableCameras();
      if (cameras != null && cameras!.isNotEmpty) {
        // Try to find front camera
        final frontCamera = cameras!.firstWhere(
              (camera) => camera.lensDirection == CameraLensDirection.front,
          orElse: () => cameras!.first,
        );

        _cameraController = CameraController(
          frontCamera,
          ResolutionPreset.medium,
          enableAudio: false,
        );

        await _cameraController!.initialize();
        if (mounted) {
          setState(() {});
        }
      }
    } catch (e) {
      debugPrint('Error initializing camera: $e');
    }
  }

  Future<void> _loadTodayRecord() async {
    try {
      setState(() => _isLoading = true);
      final records = await AttendanceService.getTodayRecords();

      setState(() {
        // Find today's check-in record if it exists
        _todayCheckIn = records.isEmpty ? null :
        records.any((record) => record.checkType == 'IN') ?
        records.firstWhere((record) => record.checkType == 'IN') :
        null;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error loading today\'s record: $e')),
        );
      }
    }
  }

  // Keep your existing _updateTime and _initCamera methods

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
        _currentDistanceInMeters = distanceInMeters.round();
        _distance = '${_currentDistanceInMeters.toString()} m';
        _hasCheckedDistance = true;
      });
    } catch (e) {
      setState(() {
        _distance = 'Error getting location';
      });
    }
  }

  Future<void> _captureAndCheckIn() async {
    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Camera not initialized')),
      );
      return;
    }

    setState(() => _isProcessing = true);

    try {
      // Get device info
      final deviceInfo = DeviceInfoPlugin();
      final androidInfo = await deviceInfo.androidInfo;
      final deviceInfoJson = {
        'device': '${androidInfo.manufacturer} ${androidInfo.model}',
        'os': 'Android ${androidInfo.version.release}'
      };

      // Capture image
      final XFile image = await _cameraController!.takePicture();
      setState(() => _capturedImage = File(image.path));

      // Send to server based on current status
      final response = _todayCheckIn == null
          ? await AttendanceService.checkIn(
        image.path,
        _currentDistanceInMeters,
        jsonEncode(deviceInfoJson),
      )
          : await AttendanceService.checkOut(
        image.path,
        _currentDistanceInMeters,
        jsonEncode(deviceInfoJson),
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(response['message'] ?? 'Action successful')),
        );
        // Reload today's record after successful check-in/out
        _loadTodayRecord();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isProcessing = false;
          _isCameraActive = false;
        });
      }
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
            if (_isCameraActive && _cameraController?.value.isInitialized == true)
              Expanded(
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    CameraPreview(_cameraController!),
                    if (_isProcessing)
                      const CircularProgressIndicator(),
                    Positioned(
                      bottom: 20,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          ElevatedButton(
                            onPressed: _isProcessing ? null : _captureAndCheckIn,
                            child: Text(_todayCheckIn == null ? 'Check In' : 'Check Out'),
                          ),
                          const SizedBox(width: 20),
                          ElevatedButton(
                            onPressed: () => setState(() => _isCameraActive = false),
                            child: const Text('Cancel'),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              )
            else ...[
              Text(
                _currentTime,
                style: const TextStyle(fontSize: 64),
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
              if (_isLoading) ...[
                const CircularProgressIndicator(),
              ] else if (_hasCheckedDistance) ...[
                ElevatedButton(
                  onPressed: _currentDistanceInMeters <= 5000
                      ? () => setState(() => _isCameraActive = true)
                      : null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 20),
                    disabledBackgroundColor: Colors.grey,
                    disabledForegroundColor: Colors.white70,
                  ),
                  child: Text(
                    _currentDistanceInMeters <= 5000
                        ? (_todayCheckIn == null ? 'CHECK IN NOW' : 'CHECK OUT NOW')
                        : 'TOO FAR FROM OFFICE',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),

                if (_todayCheckIn != null) ...[
                  const SizedBox(height: 20),
                  Text(
                    'Checked in at: ${DateFormat('HH:mm').format(_todayCheckIn!.checkTime)}',
                    style: const TextStyle(
                      fontSize: 16,
                      color: Colors.green,
                    ),
                  ),
                ],
              ],
            ],
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    super.dispose();
  }
}