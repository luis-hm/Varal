import type { components } from "@/types/api";

export type Me = components["schemas"]["Me"];
export type AuthConfig = components["schemas"]["AllauthConfigurationResponse"];
export type Authenticated = components["schemas"]["AllauthAuthenticatedResponse"];
export type Unauthenticated = components["schemas"]["AllauthAuthenticationResponse"];
export type AuthIssue = NonNullable<components["schemas"]["AllauthErrorResponse"]["errors"]>[number];
export type Login = components["schemas"]["AllauthLogin"];
export type Signup = components["schemas"]["AllauthSignup"];
export type RequestPassword = components["schemas"]["AllauthRequestPassword"];
export type ResetPassword = components["schemas"]["AllauthResetPassword"];
