/**
 * Shared application state for AI Dietitian.
 * All step modules import and mutate this single object.
 */
export const state = {
  step: 1,
  userId: 'demo-user',
  healthProfile: {},
  preferenceProfile: {},
  nutrientResponse: null,
  mealPlanResponse: null,
  mealPlanAttempted: false,
  groceryResponse: null,
  chatMessages: [],
  analyticsResponse: null,
  reportResponse: null,
  inferredConditions: [],
  ttsEnabled: false,
  coachLanguageCode: '',
};
