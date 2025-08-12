// API service for activities
export interface Activity {
  id: number;
  created_at: string;
  brand_id: string;
  name: string;
  start_time: string;
  end_time: string | null;
  execution_time_ms: number | null;
}

export interface ActivitiesResponse {
  activities: Activity[];
}

export class ApiService {
  private static baseUrl = '/api';

  static async getActivities(): Promise<Activity[]> {
    const response = await fetch(`${this.baseUrl}/activities/`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch activities: ${response.statusText}`);
    }
    
    const data: ActivitiesResponse = await response.json();
    return data.activities;
  }

  static async getRecording(activityId: number) {
    const response = await fetch(`${this.baseUrl}/activities/recordings?activity_id=${activityId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch recording: ${response.statusText}`);
    }
    
    return await response.json();
  }
}