// Prompt 模板接口文件：封装后端只读模板列表与详情接口。
import http from './http'

// Prompt 模板列表项类型
export interface PromptTemplateItem {
  template_key: string
  module: string
  task_type: string
  name: string
  description: string
  version: string
}

// Prompt 模板详情类型：包含完整 system_prompt 与 user_prompt_template。
export interface PromptTemplateDetail extends PromptTemplateItem {
  system_prompt: string
  user_prompt_template: string
}

// 获取 Prompt 模板列表。
export const promptTemplateListApi = () => {
  return http.get('/api/prompt-templates')
}

// 获取 Prompt 模板详情。
export const promptTemplateDetailApi = (templateKey: string) => {
  return http.get(`/api/prompt-templates/${templateKey}`)
}
