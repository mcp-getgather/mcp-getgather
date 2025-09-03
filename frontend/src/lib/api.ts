import createFetchClient from "openapi-fetch";
import createClient from "openapi-react-query";

import type { paths } from "@generated/api";

const fetchClient = createFetchClient<paths>({ baseUrl: "/api" });
export const $api = createClient(fetchClient);
