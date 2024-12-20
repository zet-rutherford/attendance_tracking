// lib/screens/calendar_screen.dart
import 'package:flutter/material.dart';

class CalendarScreen extends StatelessWidget {
  const CalendarScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Attendance Calendar'),
        centerTitle: true,
      ),
      body: const Center(
        child: Text('Calendar View Coming Soon'),
      ),
    );
  }
}