import apiService, { type BrandState } from "@/lib/api-service";
import { useEffect, useState } from "react";

export const useBrands = () => {
  const [brands, setBrands] = useState<BrandState[]>([]);

  const getBrands = async () => {
    apiService.fetchBrands().then((result) => {
      setBrands(result);
    });
  };

  const updateBrandEnabled = (brandId: string) => {
    const enabled = brands.find((b) => b.brand_id === brandId)?.enabled;
    setBrands(
      brands.map((b) =>
        b.brand_id === brandId ? { ...b, enabled: !enabled } : b,
      ),
    );
    apiService
      .updateBrandEnabled(brandId, !enabled)
      .then(() => {})
      .catch(() => {
        setBrands(
          brands.map((b) =>
            b.brand_id === brandId ? { ...b, enabled: !b.enabled } : b,
          ),
        );
      });
  };

  useEffect(() => {
    getBrands();
  }, []);

  return { brands, updateBrandEnabled };
};
