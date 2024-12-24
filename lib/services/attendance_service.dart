// lib/services/attendance_service.dart
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../config/env.dart';
import 'auth_service.dart';
import 'package:flutter/foundation.dart';  // Add this import

class AttendanceRecord {
  final DateTime checkTime;
  final String checkType;
  final double faceSimilarity;
  final int id;
  final double location;
  final String status;

  AttendanceRecord({
    required this.checkTime,
    required this.checkType,
    required this.faceSimilarity,
    required this.id,
    required this.location,
    required this.status,
  });

  factory AttendanceRecord.fromJson(Map<String, dynamic> json) {
    return AttendanceRecord(
      checkTime: DateTime.parse(json['check_time']),
      checkType: json['check_type'],
      faceSimilarity: json['face_similarity'].toDouble(),
      id: json['id'],
      location: json['location'].toDouble(),
      status: json['status'],
    );
  }
}

class AttendanceService {
  static Future<List<AttendanceRecord>> getDailyRecords(DateTime date) async {
    debugPrint('================== ATTENDANCE SERVICE LOG ==================');
    debugPrint('Starting to fetch attendance records');

    try {
      final token = await AuthService.getToken();
      debugPrint('Token retrieved: ${token != null ? 'Yes' : 'No'}');

      if (token == null) {
        debugPrint('No token found - throwing exception');
        throw Exception('No authentication token found');
      }

      final formattedDate = "${date.year}-${date.month}-${date.day}";
      debugPrint('Date requested: $formattedDate');
      debugPrint('API URL: ${Env.apiUrl}/api/attendance/daily-records?date=$formattedDate');

      final response = await http.get(
        Uri.parse('${Env.apiUrl}/api/attendance/daily-records?date=$formattedDate'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      debugPrint('Response status code: ${response.statusCode}');
      debugPrint('Response body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['status'] == 'success') {
          final records = (data['data'] as List)
              .map((record) => AttendanceRecord.fromJson(record))
              .toList();
          debugPrint('Successfully parsed ${records.length} records');
          return records;
        }
        throw Exception('Failed to get attendance records');
      } else {
        throw Exception('Failed to load attendance records: ${response.statusCode}');
      }
    } catch (e) {
      debugPrint('Error in getDailyRecords: $e');
      rethrow;
    } finally {
      debugPrint('======================================================');
    }
  }
}