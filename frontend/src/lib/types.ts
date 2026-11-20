export interface User {
  id: string;
  email: string;
  name: string | null;
  github_username: string | null;
  github_avatar_url: string | null;
  github_connected: boolean;
}

export interface Repository {
  id: string;
  owner: string;
  name: string;
  full_name: string;
  description: string | null;
  default_branch: string;
  selected_branch: string;
  primary_language: string | null;
  is_private: boolean;
  indexing_status: string;
  file_count: number;
  symbol_count: number;
  created_at: string;
}

export interface AvailableGithubRepo {
  github_repo_id: number;
  owner: string;
  name: string;
  full_name: string;
  description: string | null;
  default_branch: string;
  primary_language: string | null;
  is_private: boolean;
  already_connected: boolean;
}
