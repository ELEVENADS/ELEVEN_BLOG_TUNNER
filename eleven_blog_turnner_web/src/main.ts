import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

import 'tdesign-vue-next/dist/tdesign.css'
import {
  Button,
  Layout,
  Aside,
  Header,
  Content,
  Footer,
  Menu,
  MenuItem,
  Submenu,
  Card,
  Tree,
  Breadcrumb,
  BreadcrumbItem,
  Dropdown,
  DropdownMenu,
  DropdownItem,
  Form,
  FormItem,
  Input,
  InputNumber,
  Textarea,
  Table,
  Tag,
  Link,
  Space,
  Pagination,
  Dialog,
  DialogPlugin,
  Message,
  MessagePlugin,
  Loading,
  LoadingPlugin,
  ConfigProvider,
  Icon,
  Checkbox,
  Select,
  Option,
  Row,
  Col,
  Popup,
  Tooltip
} from 'tdesign-vue-next'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(Layout)
app.use(Aside)
app.use(Header)
app.use(Content)
app.use(Footer)
app.use(Button)
app.use(Menu)
app.use(MenuItem)
app.use(Submenu)
app.use(Card)
app.use(Tree)
app.use(Breadcrumb)
app.use(BreadcrumbItem)
app.use(Dropdown)
app.use(DropdownMenu)
app.use(DropdownItem)
app.use(Form)
app.use(FormItem)
app.use(Input)
app.use(InputNumber)
app.use(Textarea)
app.use(Table)
app.use(Tag)
app.use(Link)
app.use(Space)
app.use(Pagination)
app.use(Dialog)
app.use(Loading)
app.use(ConfigProvider)
app.use(Icon)
app.use(Checkbox)
app.use(Select)
app.use(Option)
app.use(Row)
app.use(Col)
app.use(Popup)
app.use(Tooltip)

app.config.globalProperties.$message = Message
app.config.globalProperties.$loading = Loading
app.config.globalProperties.$dialog = DialogPlugin
app.config.globalProperties.$notify = MessagePlugin

app.mount('#app')