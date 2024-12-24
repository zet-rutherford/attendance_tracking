// lib/screens/calendar_screen.dart
import 'package:flutter/material.dart';
import 'package:table_calendar/table_calendar.dart';
import 'package:intl/intl.dart';
import '../services/attendance_service.dart';
import 'package:flutter/foundation.dart';  // Add this import

class CalendarScreen extends StatefulWidget {
  const CalendarScreen({super.key});

  @override
  State<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends State<CalendarScreen> {
  CalendarFormat _calendarFormat = CalendarFormat.month;
  DateTime _focusedDay = DateTime.now();
  DateTime? _selectedDay;
  List<AttendanceRecord> _selectedDayRecords = [];
  bool _isLoading = false;

  Future<void> _loadDailyRecords(DateTime date) async {
    setState(() {
      _isLoading = true;
    });
    try {
      debugPrint('================== CALENDAR SCREEN LOG ==================');
      debugPrint('Loading records for date: ${date.toString()}');
      debugPrint('======================================================');
      final records = await AttendanceService.getDailyRecords(date);
      setState(() {
        _selectedDayRecords = records;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error loading records: $e')),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Attendance Calendar'),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            TableCalendar(
              firstDay: DateTime.utc(2024, 1, 1),
              lastDay: DateTime.utc(2024, 12, 31),
              focusedDay: _focusedDay,
              calendarFormat: _calendarFormat,
              selectedDayPredicate: (day) {
                return isSameDay(_selectedDay, day);
              },
              onDaySelected: (selectedDay, focusedDay) {
                setState(() {
                  _selectedDay = selectedDay;
                  _focusedDay = focusedDay;
                });
                _loadDailyRecords(selectedDay);
              },
              onFormatChanged: (format) {
                setState(() {
                  _calendarFormat = format;
                });
              },
            ),
            const SizedBox(height: 20),
            if (_selectedDay != null) ...[
              Text(
                'Selected: ${DateFormat('yyyy-MM-dd').format(_selectedDay!)}',
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              if (_isLoading)
                const CircularProgressIndicator()
              else if (_selectedDayRecords.isEmpty)
                const Text('No attendance records for this date')
              else
                Expanded(
                  child: ListView.builder(
                    itemCount: _selectedDayRecords.length,
                    itemBuilder: (context, index) {
                      final record = _selectedDayRecords[index];
                      return Card(
                        margin: const EdgeInsets.symmetric(vertical: 8),
                        child: ListTile(
                          leading: Icon(
                            record.checkType == 'IN'
                                ? Icons.login
                                : Icons.logout,
                            color: record.checkType == 'IN'
                                ? Colors.green
                                : Colors.red,
                          ),
                          title: Text(
                            '${record.checkType} - ${record.status}',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Time: ${DateFormat('HH:mm:ss').format(record.checkTime)}',
                              ),
                              Text(
                                'Face Similarity: ${(record.faceSimilarity * 100).toStringAsFixed(1)}%',
                              ),
                              Text(
                                'Distance: ${record.location.toStringAsFixed(2)} km',
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }
}