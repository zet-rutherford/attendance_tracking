// lib/services/attendance_service.dart
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../config/env.dart';
import 'auth_service.dart';
import 'package:flutter/foundation.dart';

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
  static Future<Map<String, dynamic>> checkIn(
      String imagePath,
      int distance,
      String deviceInfo,
      ) async {
    debugPrint('================== ATTENDANCE SERVICE - CHECK IN ==================');
    try {
      final token = await AuthService.getToken();
      if (token == null) {
        throw Exception('No authentication token found');
      }

      final uri = Uri.parse('${Env.apiUrl}/api/attendance/check-in');
      var request = http.MultipartRequest('POST', uri);

      request.headers.addAll({
        'Authorization': 'Bearer $token',
      });

      request.files.add(await http.MultipartFile.fromPath('image', imagePath));
      request.fields['distance'] = distance.toString();
      request.fields['device_info'] = deviceInfo;

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Check-in failed: ${response.body}');
      }
    } catch (e) {
      debugPrint('Error during check-in: $e');
      rethrow;
    }
  }

  static Future<Map<String, dynamic>> checkOut(
      String imagePath,
      int distance,
      String deviceInfo,
      ) async {
    debugPrint('================== ATTENDANCE SERVICE - CHECK OUT ==================');
    try {
      final token = await AuthService.getToken();
      if (token == null) {
        throw Exception('No authentication token found');
      }

      final uri = Uri.parse('${Env.apiUrl}/api/attendance/check-out');
      var request = http.MultipartRequest('POST', uri);

      request.headers.addAll({
        'Authorization': 'Bearer $token',
      });

      request.files.add(await http.MultipartFile.fromPath('image', imagePath));
      request.fields['distance'] = distance.toString();
      request.fields['device_info'] = deviceInfo;

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Check-out failed: ${response.body}');
      }
    } catch (e) {
      debugPrint('Error during check-out: $e');
      rethrow;
    }
  }

  static Future<List<AttendanceRecord>> getTodayRecords() async {
    debugPrint('================== ATTENDANCE SERVICE - GET TODAY RECORDS ==================');
    final today = DateTime.now();
    return getDailyRecords(today);
  }

  static Future<List<AttendanceRecord>> getDailyRecords(DateTime date) async {
    debugPrint('================== ATTENDANCE SERVICE LOG ==================');
    try {
      final token = await AuthService.getToken();
      if (token == null) {
        throw Exception('No authentication token found');
      }

      final formattedDate = "${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}";
      final uri = Uri.parse('${Env.apiUrl}/api/attendance/daily-records?date=$formattedDate');

      final response = await http.get(
        uri,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['status'] == 'success') {
          final records = (data['data'] as List)
              .map((record) => AttendanceRecord.fromJson(record))
              .toList();
          return records;
        }
        return [];
      } else {
        throw Exception('Failed to load attendance records: ${response.statusCode}');
      }
    } catch (e) {
      debugPrint('Error in getDailyRecords: $e');
      rethrow;
    }
  }
}