// API service for activities
export type Activity = {
  id: number;
  created_at: string;
  brand_id: string;
  name: string;
  start_time: string;
  end_time: string | null;
  execution_time_ms: number | null;
  recording_count: number;
  has_recording: boolean;
};

export type RecordingResponse = {
  events: RRWebEvent[];
};

export type RRWebEvent = {
  type: number;
  data: Record<string, unknown>;
  timestamp: number;
  [key: string]: unknown;
};

export class ApiService {
  private static baseUrl = "/api";

  static async getActivities(): Promise<Activity[]> {
    const response = await fetch(`${this.baseUrl}/activities/`);

    if (!response.ok) {
      throw new Error(`Failed to fetch activities: ${response.statusText}`);
    }

    const data: Activity[] = await response.json();
    return data;
  }

  static async getRecording(activityId: string): Promise<RecordingResponse> {
    const response = await fetch(`${this.baseUrl}/activities/${activityId}/recordings`);

    if (!response.ok) {
      throw new Error(`Failed to fetch recording: ${response.statusText}`);
    }

    return await response.json();
  }
}
