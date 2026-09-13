import { apiRequest } from "./api";

export type Role = "empresa" | "financiadora";

export interface Profile {
  role: Role;
  display_name: string;
  org_name: string;
}

export async function getProfiles(): Promise<Profile[]> {
  return apiRequest<Profile[]>("/api/profiles/");
}
