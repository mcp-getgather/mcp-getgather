export interface BrandState {
  brand_id: string;
  name: string;
  browser_profile_id: string | null;
  is_connected: boolean;
  enabled: boolean;
}

export class ApiService {
  private async fetcher<T>(
    endpoint: string,
    options?: RequestInit,
  ): Promise<T> {
    const response = await fetch(endpoint, {
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Fetch all brands
  async fetchBrands(): Promise<BrandState[]> {
    return this.fetcher<BrandState[]>("/station/brands");
  }

  // Update brand enabled status
  async updateBrandEnabled(
    brandId: string,
    enabled: boolean,
  ): Promise<BrandState> {
    return this.fetcher<BrandState>(`/station/brands/${brandId}`, {
      method: "PATCH",
      body: JSON.stringify({ enabled }),
    });
  }
}

const apiService = new ApiService();

export default apiService;
