import type { components } from "@/types/api";

export type Me = components["schemas"]["Me"];
export type AuthConfig = components["schemas"]["AllauthConfigurationResponse"];
export type Authenticated = components["schemas"]["AllauthAuthenticatedResponse"];
export type Unauthenticated = components["schemas"]["AllauthAuthenticationResponse"];
export type AuthIssue = NonNullable<components["schemas"]["AllauthErrorResponse"]["errors"]>[number];
export type Login = components["schemas"]["AllauthLogin"];
// allauth's static spec omits ACCOUNT_SIGNUP_FORM_CLASS fields; `nome` is optional (Q12-2).
export type Signup = components["schemas"]["AllauthSignup"] & { nome?: string };
export type RequestPassword = components["schemas"]["AllauthRequestPassword"];
export type ResetPassword = components["schemas"]["AllauthResetPassword"];
