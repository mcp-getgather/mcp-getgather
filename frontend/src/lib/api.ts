import type { paths } from "@generated/api";
import createFetchClient from "openapi-fetch";
import createClient from "openapi-react-query";

const fetchClient = createFetchClient<paths>({ baseUrl: "/api" });
export const $api = createClient(fetchClient);
